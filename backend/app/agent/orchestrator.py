from __future__ import annotations
import uuid
import time
import json
import logging
from typing import AsyncIterator, Optional, Dict, Any, List
from app.agent.state import AgentState, ToolCallInfo, ApprovalRequest
from app.agent.llm_provider import LLMProvider
from app.agent.router import IntentRouter
from app.tools.registry import get_tool_registry
from app.tools.base import ToolResult
from app.core.audit import AuditService
from app.core.config import settings

from app.guardrails.injection_detector import PromptInjectionDetector
from app.guardrails.pii_masker import PIIMasker
from app.guardrails.rbac import RBACPolicyEngine
from app.guardrails.approval_manager import get_approval_manager

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    ReAct Agent Loop Orchestrator with Enterprise Guardrails & Explicit State.
    Implements:
    1. Pre-execution guardrails (Prompt Injection detector, PII masking, RBAC validation)
    2. Two-tier fast intent routing (< 250 ms)
    3. Tool dispatch (SQL, ERP, M365, RAG) with AST parsing and schema validation
    4. Post-tool context scanning for indirect injection defense
    5. Human-in-the-loop (HITL) approval interception for write mutations
    6. Two-tier synthesis with verified citations
    7. Realtime SSE streaming
    8. Full observability in PostgreSQL audit_log
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm = llm_provider or LLMProvider()
        self.router = IntentRouter(self.llm)
        self.registry = get_tool_registry()
        self.injection_detector = PromptInjectionDetector(threshold=settings.PROMPT_INJECTION_THRESHOLD)
        self.pii_masker = PIIMasker()
        self.approval_manager = get_approval_manager()

    async def run_query_stream(
        self,
        user_query: str,
        user_role: str = "staff",
        user_id: str = "USR-STAFF-01",
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Executes the guarded ReAct agent cycle and yields SSE events.
        """
        total_start = time.perf_counter()
        t_id = trace_id or f"trace-{uuid.uuid4().hex[:12]}"
        
        state = AgentState(
            trace_id=t_id,
            session_id=session_id,
            user_id=user_id,
            user_role=user_role,
            user_query=user_query,
            cleaned_query=user_query.strip(),
        )

        yield {"event": "trace_init", "data": {"trace_id": t_id, "user_id": user_id, "user_role": user_role}}

        # ----------------------------------------------------------------------
        # Guardrail Step 1: Prompt Injection Detection (Direct)
        # ----------------------------------------------------------------------
        inj_res = self.injection_detector.detect_injection(user_query)
        if not inj_res.is_safe:
            state.is_flagged = True
            state.flagged_reason = inj_res.reason
            state.execution_status = "REJECTED"
            rejection_text = (
                f"Peringatan Keamanan: Pertanyaan Anda dibatalkan karena terindikasi mengandung "
                f"pola manipulasi/Prompt Injection ({inj_res.reason}). "
                f"Kejadian ini telah dicatat dalam log kepatuhan audit."
            )
            state.final_answer = rejection_text
            yield {
                "event": "guardrail_blocked",
                "data": {"violation": "PROMPT_INJECTION", "reason": inj_res.reason, "risk_score": inj_res.risk_score},
            }
            for word in rejection_text.split(" "):
                yield {"event": "token", "data": word + " "}

            total_lat = (time.perf_counter() - total_start) * 1000.0
            state.step_latencies["total"] = round(total_lat, 2)
            self._save_audit_log(state, tool_name=None, tool_args=None, summary=rejection_text)
            yield {"event": "done", "data": state.model_dump()}
            return

        # ----------------------------------------------------------------------
        # Guardrail Step 2: PII Masking on Input
        # ----------------------------------------------------------------------
        pii_res = self.pii_masker.scan_and_mask(user_query)
        state.cleaned_query = pii_res.sanitized_text

        # ----------------------------------------------------------------------
        # Guardrail Step 3: RBAC Pre-Check
        # ----------------------------------------------------------------------
        rbac_res = RBACPolicyEngine.validate_action(
            user_role=user_role,
            action_name="query_data",
            target_payload=user_query,
        )
        if not rbac_res.is_safe:
            state.is_flagged = True
            state.flagged_reason = rbac_res.reason
            state.execution_status = "REJECTED"
            rejection_text = f"Pemberitahuan Otorisasi: {rbac_res.reason}"
            state.final_answer = rejection_text
            yield {
                "event": "guardrail_blocked",
                "data": {"violation": "RBAC_VIOLATION", "reason": rbac_res.reason},
            }
            for word in rejection_text.split(" "):
                yield {"event": "token", "data": word + " "}

            total_lat = (time.perf_counter() - total_start) * 1000.0
            state.step_latencies["total"] = round(total_lat, 2)
            self._save_audit_log(state, tool_name=None, tool_args=None, summary=rejection_text)
            yield {"event": "done", "data": state.model_dump()}
            return

        # ----------------------------------------------------------------------
        # Step 4: Routing
        # ----------------------------------------------------------------------
        intent, confidence, router_latency = await self.router.route_query(state.cleaned_query)
        state.routed_intent = intent
        state.confidence_score = confidence
        state.step_latencies["router"] = router_latency

        yield {
            "event": "router_step",
            "data": {
                "intent": intent,
                "confidence": confidence,
                "latency_ms": router_latency,
            },
        }

        # ----------------------------------------------------------------------
        # Step 5: Handle Out-of-Scope
        # ----------------------------------------------------------------------
        if intent == "out_of_scope":
            rejection_text = (
                "Mohon maaf, OpsAgent hanya dapat membantu urusan operasional distribusi batubara "
                "PT Nusantara Coal Operations (seperti pengecekan stok batubara, status tongkang, "
                "purchase order, invoice, jadwal rapat jetty, dan SOP internal)."
            )
            state.final_answer = rejection_text
            state.execution_status = "REJECTED"
            state.is_flagged = True
            state.flagged_reason = "Pertanyaan di luar cakupan operasional perusahaan."

            for word in rejection_text.split(" "):
                yield {"event": "token", "data": word + " "}

            total_lat = (time.perf_counter() - total_start) * 1000.0
            state.step_latencies["total"] = round(total_lat, 2)
            self._save_audit_log(state, tool_name=None, tool_args=None, summary=rejection_text)
            yield {"event": "done", "data": state.model_dump()}
            return

        # ----------------------------------------------------------------------
        # Step 6: Tool Execution
        # ----------------------------------------------------------------------
        tool_start = time.perf_counter()
        tool_res: Optional[ToolResult] = None
        executed_tool_name = None
        executed_args: Dict[str, Any] = {}

        if intent == "sql_query":
            executed_tool_name = "sql_query"
            executed_args = self._generate_sql_args(state.cleaned_query)
            yield {"event": "tool_call", "data": {"tool": "sql_query", "arguments": executed_args}}

            sql_tool = self.registry.get_tool("sql_query")
            if sql_tool:
                tool_res = await sql_tool.execute(**executed_args)

        elif intent == "erp_api":
            executed_tool_name = "erp_api"
            executed_args = self._generate_erp_args(state.cleaned_query, user_role)
            yield {"event": "tool_call", "data": {"tool": "erp_api", "arguments": executed_args}}

            erp_tool = self.registry.get_tool("erp_api")
            if erp_tool:
                tool_res = await erp_tool.execute(**executed_args)

        elif intent == "m365":
            executed_tool_name = "m365"
            executed_args = self._generate_m365_args(state.cleaned_query)
            yield {"event": "tool_call", "data": {"tool": "m365", "arguments": executed_args}}

            m365_tool = self.registry.get_tool("m365")
            if m365_tool:
                tool_res = await m365_tool.execute(**executed_args)

        elif intent == "search_docs":
            executed_tool_name = "search_docs"
            executed_args = {"query": state.cleaned_query, "top_k": 3}
            yield {"event": "tool_call", "data": {"tool": "search_docs", "arguments": executed_args}}

            rag_tool = self.registry.get_tool("search_docs")
            if rag_tool:
                tool_res = await rag_tool.execute(**executed_args)

        tool_latency = (time.perf_counter() - tool_start) * 1000.0
        state.step_latencies["tool_execution"] = round(tool_latency, 2)

        if tool_res:
            # ------------------------------------------------------------------
            # Guardrail: Indirect Injection Check on Document Chunks
            # ------------------------------------------------------------------
            if executed_tool_name == "search_docs" and isinstance(tool_res.output, dict):
                chunks = tool_res.output.get("chunks", [])
                safe_chunks = []
                for chk in chunks:
                    doc_inj = self.injection_detector.detect_injection(chk.get("content", ""), is_document=True)
                    if not doc_inj.is_safe:
                        logger.warning(f"Sanitizing indirect injection from doc {chk.get('doc_code')}")
                        chk["content"] = "[REDACTED_INDIRECT_PROMPT_INJECTION]"
                    safe_chunks.append(chk)
                tool_res.output["chunks"] = safe_chunks

            state.tool_results.append(tool_res)
            yield {
                "event": "tool_result",
                "data": {
                    "tool": tool_res.tool_name,
                    "is_success": tool_res.is_success,
                    "summary": tool_res.summary,
                    "latency_ms": tool_res.latency_ms,
                    "output": tool_res.output,
                },
            }

            # Extract citations if search_docs tool was called
            if executed_tool_name == "search_docs" and isinstance(tool_res.output, dict):
                state.citations = tool_res.output.get("citations", [])
                if state.citations:
                    yield {"event": "citations", "data": state.citations}

            # Check if write action triggered Human-in-the-Loop approval
            if tool_res.requires_approval or (isinstance(tool_res.output, dict) and tool_res.output.get("requires_approval")):
                state.requires_approval = True
                approval_action = self.approval_manager.register_approval_request(
                    trace_id=t_id,
                    action_type="CREATE_PURCHASE_ORDER",
                    title="Persetujuan Penerbitan Purchase Order Baru",
                    description=(
                        f"Draft PO diterbitkan oleh {user_role}. "
                        f"Nilai atau tonase membutuhkan verifikasi Manager sesuai SOP-PROC-003."
                    ),
                    payload=tool_res.output,
                    requester_id=user_id,
                    requester_role=user_role,
                )
                appr_req = ApprovalRequest(
                    approval_id=approval_action.approval_id,
                    action_type=approval_action.action_type,
                    title=approval_action.title,
                    description=approval_action.description,
                    payload=approval_action.payload,
                    required_role="manager",
                    status="PENDING",
                )
                state.pending_approval = appr_req
                state.execution_status = "PENDING_APPROVAL"
                yield {"event": "approval_required", "data": appr_req.model_dump()}

        # ----------------------------------------------------------------------
        # Step 7: Two-Tier Synthesis (Token Streaming)
        # ----------------------------------------------------------------------
        synth_start = time.perf_counter()
        summary_text = tool_res.summary if tool_res else "Tidak ada eksekusi tool."
        
        if tool_res and tool_res.is_success and tool_res.output is not None:
            formatted_data_str = self._format_tool_output_for_synthesis(tool_res.tool_name, tool_res.output)
            summary_text = f"{tool_res.summary}\n\nDetail Data:\n{formatted_data_str}"

        # Mask PII in summary text before sending to synthesis model
        summary_text, _ = self.pii_masker.mask_text(summary_text)

        answer_chunks: List[str] = []
        async for token in self.llm.stream_synthesis(
            user_query=state.cleaned_query,
            tool_results_summary=summary_text,
            citations=state.citations,
            user_role=user_role,
        ):
            # Mask PII on output stream tokens
            masked_token, _ = self.pii_masker.mask_text(token)
            answer_chunks.append(masked_token)
            yield {"event": "token", "data": masked_token}

        state.final_answer = "".join(answer_chunks)
        synth_latency = (time.perf_counter() - synth_start) * 1000.0
        state.step_latencies["synthesis"] = round(synth_latency, 2)

        # ----------------------------------------------------------------------
        # Step 8: Metrics & Observability
        # ----------------------------------------------------------------------
        total_lat = (time.perf_counter() - total_start) * 1000.0
        state.step_latencies["total"] = round(total_lat, 2)

        state.prompt_tokens = len(state.user_query.split()) + len(summary_text.split()) + 80
        state.completion_tokens = len(state.final_answer.split())
        state.total_tokens = state.prompt_tokens + state.completion_tokens
        state.estimated_cost_usd = self.llm.calculate_cost(
            state.prompt_tokens,
            state.completion_tokens,
            settings.SYNTHESIS_MODEL,
        )

        self._save_audit_log(
            state,
            tool_name=executed_tool_name,
            tool_args=executed_args,
            summary=tool_res.summary if tool_res else "",
        )

        yield {"event": "done", "data": state.model_dump()}

    def _generate_sql_args(self, query: str) -> Dict[str, Any]:
        """Maps natural language query to sanitized SQL query for coal operations."""
        q = query.lower()
        if "stok" in q or "stockpile" in q or "inventory" in q:
            return {
                "query": (
                    "SELECT s.stockpile_name, s.location, i.grade, i.tonnage_mt, "
                    "i.calorific_value_gar, i.temperature_celsius "
                    "FROM stockpiles s JOIN coal_inventory i ON s.id = i.stockpile_id"
                )
            }
        elif "tongkang" in q or "barge" in q or "kirim" in q or "laycan" in q:
            return {
                "query": (
                    "SELECT shipment_number, coal_grade, tonnage_loaded_mt, "
                    "origin_jetty, destination_port, status "
                    "FROM barge_shipments"
                )
            }
        elif "buyer" in q or "pelanggan" in q or "customer" in q:
            return {
                "query": "SELECT customer_code, company_name, industry_type, delivery_port FROM customers"
            }
        elif "supplier" in q or "tambang" in q:
            return {
                "query": "SELECT supplier_code, company_name, concession_area, status FROM suppliers"
            }
        else:
            return {
                "query": "SELECT stockpile_name, location, current_stock_mt, status FROM stockpiles"
            }

    def _generate_erp_args(self, query: str, user_role: str) -> Dict[str, Any]:
        """Maps natural language query to ERP action and parameters."""
        q = query.lower()
        is_create_po = (
            "buat po" in q
            or "create po" in q
            or "draft po" in q
            or "draf po" in q
            or "order pembelian" in q
            or "terbitkan draft purchase order" in q
            or "pembelian solar" in q
            or ("purchase order" in q and any(w in q for w in ["buat", "terbit", "aju", "draft", "draf", "order"]))
            or ("po" in q and any(w in q for w in ["buat", "terbit", "aju", "draft", "draf", "order"]))
        )
        if is_create_po:
            return {
                "action": "create_po_draft",
                "supplier_code": "SUP-KPC-01",
                "supplier_name": "PT Kaltim Prima Mining Concession",
                "delivery_jetty": "Palaran Jetty, Samarinda",
                "grade": "GAR 4200",
                "quantity_mt": 7500.0,
                "unit_price_usd": 58.50,
                "notes": f"Permohonan draft PO via OpsAgent oleh {user_role}",
                "user_role": user_role,
            }
        elif "invoice" in q or "tagihan" in q or "overdue" in q or "piutang" in q:
            overdue_only = "overdue" in q or "macet" in q or "unpaid" in q or "belum dibayar" in q
            return {"action": "get_invoices", "overdue_only": overdue_only}
        elif "tongkang" in q or "shipment" in q or "kapal" in q:
            return {"action": "get_shipments"}
        else:
            return {"action": "get_purchase_order"}

    def _generate_m365_args(self, query: str) -> Dict[str, Any]:
        """Maps natural language query to M365 action parameters."""
        q = query.lower()
        if "email" in q or "kirim" in q:
            return {
                "action": "draft_email",
                "subject": "Pemberitahuan Status Muatan Tongkang Batubara",
                "body_text": "Yth. Rekan Operasional, terlampir update draught survey dan jadwal keberangkatan tongkang.",
                "to_recipients": ["loading.master@nusantaracoal.com"],
            }
        elif "rapat" in q or "buat event" in q or "jadwal meeting" in q:
            return {
                "action": "create_calendar_event",
                "event_subject": "Koordinasi Laycan Tongkang Batubara",
                "location": "Jetty Control Room",
            }
        else:
            return {"action": "check_availability"}

    def _format_tool_output_for_synthesis(self, tool_name: str, output: Any) -> str:
        if isinstance(output, list):
            lines = []
            for item in output[:5]:
                if isinstance(item, dict):
                    formatted_item = ", ".join(f"{k}: {v}" for k, v in item.items() if v is not None)
                    lines.append(f"- {formatted_item}")
                else:
                    lines.append(f"- {str(item)}")
            return "\n".join(lines)
        elif isinstance(output, dict):
            if "formatted_context" in output:
                return output["formatted_context"]
            return json.dumps(output, indent=2, ensure_ascii=False, default=str)
        return str(output)

    def _save_audit_log(
        self,
        state: AgentState,
        tool_name: Optional[str],
        tool_args: Optional[Dict[str, Any]],
        summary: str,
    ) -> None:
        """Persists audit log with masked PII to DB."""
        masked_query, query_pii_count = self.pii_masker.mask_text(state.user_query)
        masked_summary, sum_pii_count = self.pii_masker.mask_text(summary[:500])

        AuditService.record_audit_entry(
            trace_id=state.trace_id,
            session_id=state.session_id,
            user_id=state.user_id,
            user_role=state.user_role,
            user_query=masked_query,
            routed_intent=state.routed_intent,
            tool_name=tool_name,
            tool_arguments=tool_args,
            tool_result_summary=masked_summary,
            execution_status=state.execution_status,
            latency_ms=state.step_latencies.get("total", 0.0),
            prompt_tokens=state.prompt_tokens,
            completion_tokens=state.completion_tokens,
            total_tokens=state.total_tokens,
            estimated_cost_usd=state.estimated_cost_usd,
            pii_masked=(query_pii_count + sum_pii_count > 0),
            guardrail_flagged=state.is_flagged,
            guardrail_reason=state.flagged_reason,
        )


_global_orchestrator: Optional[AgentOrchestrator] = None


def get_agent_orchestrator() -> AgentOrchestrator:
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = AgentOrchestrator()
    return _global_orchestrator
