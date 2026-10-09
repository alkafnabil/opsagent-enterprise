import pytest
from app.guardrails.approval_manager import get_approval_manager


@pytest.mark.asyncio
async def test_full_approval_lifecycle():
    mgr = get_approval_manager()

    # 1. Staff creates draft PO request
    payload = {
        "po_number": "PO-2026-0099",
        "supplier_code": "SUP-KPC-01",
        "quantity_mt": 10000.0,
        "total_amount_usd": 585000.0,
        "status": "DRAFT",
    }
    action = mgr.register_approval_request(
        trace_id="trace-test-appr-01",
        action_type="CREATE_PURCHASE_ORDER",
        title="Penerbitan PO Batubara 10.000 MT",
        description="PO alokasi PLTU Suralaya",
        payload=payload,
        requester_id="USR-DIMAS",
        requester_role="staff",
    )
    assert action.approval_id.startswith("APPR-")
    assert action.status == "PENDING"

    # Verify listed in pending
    pending_list = mgr.list_pending_approvals()
    assert any(a.approval_id == action.approval_id for a in pending_list)

    # 2. Staff attempts to approve -> Must raise PermissionError
    with pytest.raises(PermissionError):
        await mgr.resolve_approval(
            approval_id=action.approval_id,
            decision="APPROVE",
            decided_by="staff_dimas",
            user_role="staff",
        )

    # 3. Manager approves -> Successful resolution
    decision_resp = await mgr.resolve_approval(
        approval_id=action.approval_id,
        decision="APPROVE",
        decided_by="MGR-HENDRA",
        user_role="manager",
        manager_notes="Telah diverifikasi sesuai kuota bulanan PLN",
    )
    assert decision_resp.status == "APPROVED"
    assert decision_resp.resolved_by == "MGR-HENDRA"

    # Verify no longer in pending list
    pending_after = mgr.list_pending_approvals()
    assert not any(a.approval_id == action.approval_id for a in pending_after)
