from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    @staticmethod
    def record_audit_entry(
        trace_id: str,
        user_id: str,
        user_role: str,
        user_query: str,
        routed_intent: Optional[str],
        tool_name: Optional[str],
        tool_arguments: Optional[Dict[str, Any]],
        tool_result_summary: Optional[str],
        execution_status: str,
        latency_ms: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
        pii_masked: bool = False,
        guardrail_flagged: bool = False,
        guardrail_reason: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Optional[int]:
        """Records an execution event to the PostgreSQL audit_log table."""
        try:
            with SessionLocal() as db:
                entry = AuditLog(
                    trace_id=trace_id,
                    session_id=session_id,
                    user_id=user_id,
                    user_role=user_role,
                    user_query=user_query,
                    routed_intent=routed_intent,
                    tool_name=tool_name,
                    tool_arguments=tool_arguments,
                    tool_result_summary=tool_result_summary,
                    execution_status=execution_status,
                    latency_ms=latency_ms,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=estimated_cost_usd,
                    pii_masked=pii_masked,
                    guardrail_flagged=guardrail_flagged,
                    guardrail_reason=guardrail_reason,
                )
                db.add(entry)
                db.commit()
                db.refresh(entry)
                return entry.id
        except Exception as e:
            logger.warning(f"Gagal mencatat audit log ke DB ({e}). Mencatat ke fallback log.")
            logger.info(
                f"[AUDIT] trace={trace_id} user={user_id} role={user_role} tool={tool_name} "
                f"lat={latency_ms:.1f}ms status={execution_status}"
            )
            return None

    @staticmethod
    def get_recent_logs(limit: int = 50, trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve recent audit logs for observability inspection."""
        try:
            with SessionLocal() as db:
                query = db.query(AuditLog)
                if trace_id:
                    query = query.filter(AuditLog.trace_id == trace_id)
                entries = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
                return [
                    {
                        "id": e.id,
                        "trace_id": e.trace_id,
                        "user_id": e.user_id,
                        "user_role": e.user_role,
                        "user_query": e.user_query,
                        "routed_intent": e.routed_intent,
                        "tool_name": e.tool_name,
                        "tool_arguments": e.tool_arguments,
                        "tool_result_summary": e.tool_result_summary,
                        "execution_status": e.execution_status,
                        "latency_ms": float(e.latency_ms),
                        "total_tokens": e.total_tokens,
                        "estimated_cost_usd": float(e.estimated_cost_usd),
                        "pii_masked": e.pii_masked,
                        "guardrail_flagged": e.guardrail_flagged,
                        "created_at": e.created_at.isoformat() if e.created_at else None,
                    }
                    for e in entries
                ]
        except Exception as e:
            logger.warning(f"Error reading audit logs from DB: {e}")
            return []
