from __future__ import annotations
import json
import logging
from typing import Optional, List, Dict, Any, Literal
from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agent.orchestrator import get_agent_orchestrator
from app.core.audit import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["Chat & Agent Orchestration"])


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Pertanyaan operasional dalam bahasa Indonesia")
    user_role: Literal["staff", "manager"] = Field("staff", description="Peran pengguna: 'staff' atau 'manager'")
    user_id: str = Field("USR-STAFF-01", description="ID pengguna yang bertanya")
    trace_id: Optional[str] = Field(None, description="Optional custom trace ID")
    session_id: Optional[str] = Field(None, description="Optional session ID")


@router.post("/chat")
async def chat_streaming_endpoint(req: ChatRequest):
    """
    Streaming SSE endpoint for OpsAgent chat.
    Emits events: router_step, tool_call, tool_result, approval_required, token, citations, done.
    """
    orchestrator = get_agent_orchestrator()

    async def sse_event_generator():
        try:
            async for event_obj in orchestrator.run_query_stream(
                user_query=req.query,
                user_role=req.user_role,
                user_id=req.user_id,
                trace_id=req.trace_id,
                session_id=req.session_id,
            ):
                event_name = event_obj.get("event", "message")
                event_data = event_obj.get("data", "")
                
                # Format SSE protocol: event: ...\ndata: ...\n\n
                if isinstance(event_data, (dict, list)):
                    data_str = json.dumps(event_data, ensure_ascii=False, default=str)
                else:
                    data_str = str(event_data)

                yield f"event: {event_name}\ndata: {data_str}\n\n"
        except Exception as exc:
            logger.error(f"Error in SSE stream: {exc}")
            err_payload = json.dumps({"error": str(exc)}, ensure_ascii=False)
            yield f"event: error\ndata: {err_payload}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/sync")
async def chat_synchronous_endpoint(req: ChatRequest):
    """
    Synchronous endpoint executing the full agent loop.
    Returns complete final AgentState with tool traces and citations (ideal for eval runner).
    """
    orchestrator = get_agent_orchestrator()
    final_state = None

    async for event_obj in orchestrator.run_query_stream(
        user_query=req.query,
        user_role=req.user_role,
        user_id=req.user_id,
        trace_id=req.trace_id,
        session_id=req.session_id,
    ):
        if event_obj["event"] == "done":
            final_state = event_obj["data"]

    if not final_state:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal mengeksekusi agent loop.",
        )
    return final_state


@router.get("/audit-logs", tags=["Observability"])
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=200, description="Jumlah log maksimal"),
    trace_id: Optional[str] = Query(None, description="Filter berdasarkan trace ID"),
):
    """Retrieve audit log records for monitoring and compliance."""
    logs = AuditService.get_recent_logs(limit=limit, trace_id=trace_id)
    return {"total": len(logs), "logs": logs}
