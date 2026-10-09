from __future__ import annotations
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from app.tools.base import ToolResult


class ToolCallInfo(BaseModel):
    call_id: str
    tool_name: str
    arguments: Dict[str, Any]


class ApprovalRequest(BaseModel):
    approval_id: str
    action_type: str = "CREATE_PURCHASE_ORDER"
    title: str
    description: str
    payload: Dict[str, Any]
    required_role: Literal["manager", "director"] = "manager"
    status: Literal["PENDING", "APPROVED", "REJECTED"] = "PENDING"


class AgentState(BaseModel):
    trace_id: str
    session_id: Optional[str] = None
    user_id: str = "USR-STAFF-01"
    user_role: Literal["staff", "manager"] = "staff"
    user_query: str
    cleaned_query: str = ""
    
    routed_intent: Optional[str] = None
    confidence_score: float = 1.0
    
    tool_calls: List[ToolCallInfo] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)
    
    requires_approval: bool = False
    pending_approval: Optional[ApprovalRequest] = None
    
    citations: List[str] = Field(default_factory=list)
    final_answer: str = ""
    
    step_latencies: Dict[str, float] = Field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    
    is_flagged: bool = False
    flagged_reason: Optional[str] = None
    execution_status: Literal["SUCCESS", "FAILED", "PENDING_APPROVAL", "REJECTED"] = "SUCCESS"
