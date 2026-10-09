from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Numeric,
    Text,
    Integer,
    Boolean,
    DateTime,
    JSON,
)
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True, index=True, autoincrement=True)
    trace_id = Column(String(64), nullable=False, index=True)
    session_id = Column(String(64), nullable=True)
    user_id = Column(String(50), nullable=False, index=True)
    user_role = Column(String(20), nullable=False) # 'staff', 'manager'
    user_query = Column(Text, nullable=False)
    routed_intent = Column(String(50), nullable=True)
    tool_name = Column(String(50), nullable=True)
    tool_arguments = Column(JSON, nullable=True)
    tool_result_summary = Column(Text, nullable=True)
    execution_status = Column(String(20), nullable=False) # 'SUCCESS', 'FAILED', 'PENDING_APPROVAL', 'REJECTED'
    latency_ms = Column(Numeric(10, 2), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Numeric(10, 6), default=0.000000)
    pii_masked = Column(Boolean, default=False)
    guardrail_flagged = Column(Boolean, default=False)
    guardrail_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
