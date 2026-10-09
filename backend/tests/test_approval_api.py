from fastapi.testclient import TestClient
from app.main import app
from app.guardrails.approval_manager import get_approval_manager

client = TestClient(app)


def test_approval_api_endpoints():
    mgr = get_approval_manager()
    action = mgr.register_approval_request(
        trace_id="trace-api-test",
        action_type="CREATE_PURCHASE_ORDER",
        title="PO Pengadaan Batubara Jetty Trisakti",
        description="Draft alokasi Trisakti",
        payload={"po_number": "PO-2026-0098", "status": "DRAFT"},
        requester_id="USR-STAFF-02",
        requester_role="staff",
    )
    appr_id = action.approval_id

    # 1. GET list approvals
    get_res = client.get("/api/v1/approvals")
    assert get_res.status_code == 200
    data = get_res.json()
    assert len(data) >= 1
    assert any(item["approval_id"] == appr_id for item in data)

    # 2. GET detail approval
    detail_res = client.get(f"/api/v1/approvals/{appr_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["approval_id"] == appr_id

    # 3. Staff attempts decision -> 403 Forbidden
    staff_payload = {
        "decision": "APPROVE",
        "decided_by": "staff_budi",
        "user_role": "staff",
        "manager_notes": "Mencoba approve",
    }
    err_res = client.post(f"/api/v1/approvals/{appr_id}/decision", json=staff_payload)
    assert err_res.status_code == 403
    assert "tidak memiliki wewenang" in err_res.json()["detail"].lower() or "akses ditolak" in err_res.json()["detail"].lower()

    # 4. Manager approves -> 200 OK
    manager_payload = {
        "decision": "APPROVE",
        "decided_by": "MGR-HENDRA",
        "user_role": "manager",
        "manager_notes": "Disetujui secara resmi",
    }
    ok_res = client.post(f"/api/v1/approvals/{appr_id}/decision", json=manager_payload)
    assert ok_res.status_code == 200
    res_data = ok_res.json()
    assert res_data["status"] == "APPROVED"
    assert res_data["resolved_by"] == "MGR-HENDRA"
