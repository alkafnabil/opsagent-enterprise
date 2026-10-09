from __future__ import annotations
import re
from typing import Tuple
from app.guardrails.models import GuardrailCheckResult


class PIIMasker:
    """
    Automated Indonesian PII Masking Engine.
    Detects and masks:
    1. NIK (Nomor Induk Kependudukan - 16 digit angka)
    2. Indonesian Mobile Phone (+628xx, 628xx, 08xx)
    3. Corporate & Personal Emails
    Applied to audit logs and final assistant output.
    """

    # Regex Patterns
    # NIK: exactly 16 consecutive digits or formatted 16 digits
    NIK_REGEX = re.compile(r"\b([1-9]\d{5})(\d{6})(\d{4})\b")

    # Indonesian Phone: (08xx or +628xx or 628xx) with optional hyphens/spaces
    PHONE_REGEX = re.compile(r"(\+?628\d{1,2}|08\d{1,2})[-.\s]?\d{3,4}[-.\s]?(\d{4})\b")

    # Email
    EMAIL_REGEX = re.compile(r"\b([A-Za-z0-9._%+-]{1,3})[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b")

    def mask_text(self, text: str) -> Tuple[str, int]:
        """
        Masks all detected PII in text string.
        Returns (masked_text, total_pii_count).
        """
        if not text:
            return text, 0

        masked_count = 0

        # 1. Mask NIK: preserve first 6 and last 4, mask middle 6 digits
        def replace_nik(m: re.Match) -> str:
            nonlocal masked_count
            masked_count += 1
            return f"{m.group(1)}******{m.group(3)}"

        result = self.NIK_REGEX.sub(replace_nik, text)

        # 2. Mask Phone Number: preserve prefix (08xx / +628xx) and last 4 digits
        def replace_phone(m: re.Match) -> str:
            nonlocal masked_count
            masked_count += 1
            return f"{m.group(1)}****{m.group(2)}"

        result = self.PHONE_REGEX.sub(replace_phone, result)

        # 3. Mask Email: preserve first 2-3 characters and domain
        def replace_email(m: re.Match) -> str:
            nonlocal masked_count
            masked_count += 1
            return f"{m.group(1)}***{m.group(2)}"

        result = self.EMAIL_REGEX.sub(replace_email, result)

        return result, masked_count

    def scan_and_mask(self, text: str) -> GuardrailCheckResult:
        masked_text, count = self.mask_text(text)
        return GuardrailCheckResult(
            is_safe=True,
            violation_type="PII_DETECTED" if count > 0 else "NONE",
            risk_score=0.2 if count > 0 else 0.0,
            reason=f"Terdeteksi {count} entitas PII yang telah disamarkan." if count > 0 else None,
            sanitized_text=masked_text,
            masked_items_count=count,
        )
