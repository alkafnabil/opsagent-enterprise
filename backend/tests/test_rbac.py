import pytest
from app.guardrails.rbac import RBACPolicyEngine


def test_rbac_approval_action_restriction():
    # Staff cannot approve PO
    res_staff = RBACPolicyEngine.validate_action(user_role="staff", action_name="approve_po")
    assert res_staff.is_safe is False
    assert res_staff.violation_type == "RBAC_VIOLATION"
    assert "SOP-PROC-003" in res_staff.reason

    # Manager can approve PO
    res_mgr = RBACPolicyEngine.validate_action(user_role="manager", action_name="approve_po")
    assert res_mgr.is_safe is True
    assert res_mgr.violation_type == "NONE"


def test_rbac_credit_limit_confidentiality():
    # Staff asking for credit limit
    query_credit = "Tampilkan credit_limit_usd untuk semua pelanggan PLN dan Semen"
    res_staff = RBACPolicyEngine.validate_action(
        user_role="staff",
        action_name="query_data",
        target_payload=query_credit,
    )
    assert res_staff.is_safe is False
    assert "limit kredit" in res_staff.reason.lower() or "credit" in res_staff.reason.lower()

    # Manager asking for credit limit
    res_mgr = RBACPolicyEngine.validate_action(
        user_role="manager",
        action_name="query_data",
        target_payload=query_credit,
    )
    assert res_mgr.is_safe is True
