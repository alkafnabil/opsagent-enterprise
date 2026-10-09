from __future__ import annotations
import uuid
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional
from app.guardrails.models import ApprovalAction, ApprovalDecisionResponse
from app.guardrails.rbac import RBACPolicyEngine
from app.core.audit import AuditService

logger = logging.getLogger(__name__)


class ApprovalManager:
    """
    Stateful Human-in-the-Loop (HITL) Approval Coordinator.
    Stores and mediates write action approval workflows (e.g. Purchase Order issuance).
    """

    def __init__(self):
        # Store keyed by approval_id
        self._approvals: Dict[str, ApprovalAction] = {}

    def register_approval_request(
        self,
        trace_id: str,
        action_type: str,
        title: str,
        description: str,
        payload: Dict,
        requester_id: str = "USR-STAFF-01",
        requester_role: str = "staff",
    ) -> ApprovalAction:
        approval_id = f"APPR-{uuid.uuid4().hex[:8].upper()}"
        action = ApprovalAction(
            approval_id=approval_id,
            trace_id=trace_id,
            action_type=action_type,
            requester_id=requester_id,
            requester_role=requester_role,
            required_role="manager",
            title=title,
            description=description,
            payload=payload,
            status="PENDING",
            created_at=datetime.now(timezone.utc),
        )
        self._approvals[approval_id] = action
        logger.info(f"Registered new approval request: {approval_id} ({action_type}) by {requester_role}")
        return action

    def list_pending_approvals(self) -> List[ApprovalAction]:
        return [a for a in self._approvals.values() if a.status == "PENDING"]

    def list_all_approvals(self) -> List[ApprovalAction]:
        return sorted(self._approvals.values(), key=lambda x: x.created_at, reverse=True)

    def get_approval(self, approval_id: str) -> Optional[ApprovalAction]:
        return self._approvals.get(approval_id)

    async def resolve_approval(
        self,
        approval_id: str,
        decision: str, # "APPROVE" or "REJECT"
        decided_by: str,
        user_role: str,
        manager_notes: Optional[str] = None,
    ) -> ApprovalDecisionResponse:
        action = self._approvals.get(approval_id)
        if not action:
            raise ValueError(f"Approval request '{approval_id}' tidak ditemukan.")

        if action.status != "PENDING":
            raise ValueError(f"Approval request '{approval_id}' sudah berstatus '{action.status}'.")

        # 1. RBAC check: Only Manager can approve or reject
        rbac_res = RBACPolicyEngine.validate_action(user_role=user_role, action_name="approve_po")
        if not rbac_res.is_safe:
            raise PermissionError(rbac_res.reason)

        now = datetime.now(timezone.utc)
        action.resolved_by = decided_by
        action.resolved_at = now
        action.resolution_notes = manager_notes

        erp_result = None
        if decision.upper() == "APPROVE":
            action.status = "APPROVED"
            
            # Execute mutation in ERP if payload contains PO number
            po_number = action.payload.get("po_number")
            if po_number:
                from mock_erp.database import approve_purchase_order
                approved_po = approve_purchase_order(
                    po_number=po_number,
                    approved_by=decided_by,
                    notes=manager_notes,
                )
                if approved_po:
                    erp_result = approved_po.model_dump()
            
            msg = f"Aksi '{action.title}' berhasil disetujui (APPROVED) oleh Manager {decided_by}."
            exec_status = "APPROVED"
        else:
            action.status = "REJECTED"
            msg = f"Aksi '{action.title}' ditolak (REJECTED) oleh Manager {decided_by}."
            exec_status = "REJECTED"

        # Record audit log for compliance
        AuditService.record_audit_entry(
            trace_id=action.trace_id,
            user_id=decided_by,
            user_role=user_role,
            user_query=f"[HITL_DECISION] {decision.upper()} approval {approval_id}",
            routed_intent="approval_resolution",
            tool_name="approval_manager",
            tool_arguments={"approval_id": approval_id, "decision": decision, "notes": manager_notes},
            tool_result_summary=msg,
            execution_status=exec_status,
            latency_ms=10.0,
        )

        return ApprovalDecisionResponse(
            approval_id=approval_id,
            status=action.status,
            action_type=action.action_type,
            resolved_by=decided_by,
            resolved_at=now,
            erp_result=erp_result,
            message=msg,
        )


_global_approval_manager: Optional[ApprovalManager] = None


def get_approval_manager() -> ApprovalManager:
    global _global_approval_manager
    if _global_approval_manager is None:
        _global_approval_manager = ApprovalManager()
    return _global_approval_manager
