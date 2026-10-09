from __future__ import annotations
import re
from typing import Optional, Literal
from app.guardrails.models import GuardrailCheckResult


class RBACPolicyEngine:
    """
    Role-Based Access Control (RBAC) Engine.
    Roles:
    - 'staff': Operational inquiries, create draft PO (write approval required).
               Restricted from approving POs or accessing sensitive credit limit figures.
    - 'manager': Full administrative, approval, and financial credit access.
    """

    CONFIDENTIAL_COLUMNS = ["credit_limit_usd"]

    @classmethod
    def validate_action(
        cls,
        user_role: Literal["staff", "manager"],
        action_name: str,
        target_payload: Optional[str] = None,
    ) -> GuardrailCheckResult:
        role = user_role.lower()

        # 1. Staff trying to perform Manager-only approval
        if action_name in ["approve_po", "approve_purchase_order", "reject_po"]:
            if role != "manager":
                return GuardrailCheckResult(
                    is_safe=False,
                    violation_type="RBAC_VIOLATION",
                    risk_score=0.9,
                    reason=(
                        f"Akses Ditolak: Peran '{role}' tidak memiliki wewenang untuk menyetujui (Approve) "
                        f"Purchase Order. Aksi ini memerlukan wewenang 'manager' sesuai SOP-PROC-003."
                    ),
                    sanitized_text="[REDACTED_RBAC_UNAUTHORIZED]",
                )

        # 2. Staff trying to query confidential credit limits
        if target_payload and role != "manager":
            payload_lower = target_payload.lower()
            for col in cls.CONFIDENTIAL_COLUMNS:
                if col in payload_lower or "credit_limit" in payload_lower or "limit kredit" in payload_lower:
                    return GuardrailCheckResult(
                        is_safe=False,
                        violation_type="RBAC_VIOLATION",
                        risk_score=0.85,
                        reason=(
                            f"Akses Ditolak: Data limit kredit pelanggan bersifat rahasia keuangan "
                            f"dan hanya dapat diakses oleh peran 'manager' per SOP-FIN-004."
                        ),
                        sanitized_text="[REDACTED_CONFIDENTIAL_FINANCIAL_DATA]",
                    )

        return GuardrailCheckResult(
            is_safe=True,
            violation_type="NONE",
            risk_score=0.0,
            sanitized_text=target_payload or "",
        )
