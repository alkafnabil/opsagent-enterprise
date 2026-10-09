from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class GuardrailCheckResult(BaseModel):
    is_safe: bool = True
    violation_type: Optional[
        Literal["NONE", "PROMPT_INJECTION", "PII_DETECTED", "RBAC_VIOLATION", "OUT_OF_SCOPE"]
    ] = "NONE"
    risk_score: float = Field(0.0, ge=0.0, le=1.0)
    reason: Optional[str] = None
    sanitized_text: str = ""
    masked_items_count: int = 0


class ApprovalAction(BaseModel):
    approval_id: str
    trace_id: str
    action_type: str = "CREATE_PURCHASE_ORDER"
    requester_id: str
    requester_role: str
    required_role: str = "manager"
    title: str
    description: str
    payload: Dict[str, Any]
    status: Literal["PENDING", "APPROVED", "REJECTED"] = "PENDING"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    decision: Literal["APPROVE", "REJECT"] = Field(..., description="'APPROVE' atau 'REJECT'")
    decided_by: str = Field(..., min_length=3, description="Nama atau ID Manager yang menyetujui")
    user_role: Literal["staff", "manager"] = Field(..., description="Role user pemutus ('manager' diperlukan)")
    manager_notes: Optional[str] = Field(None, description="Alasan / catatan persetujuan")


class ApprovalDecisionResponse(BaseModel):
    approval_id: str
    status: Literal["APPROVED", "REJECTED"]
    action_type: str
    resolved_by: str
    resolved_at: datetime
    erp_result: Optional[Dict[str, Any]] = None
    message: str
