from __future__ import annotations
import re
import logging
from typing import Tuple, List
from app.core.config import settings
from app.guardrails.models import GuardrailCheckResult

logger = logging.getLogger(__name__)

# Direct & Indirect Prompt Injection Signatures (Indonesian & English)
_INJECTION_PATTERNS = [
    # Override & Jailbreak instructions
    (r"\b(?:ignore|abaikan|lupakan)\s+(?:all\s+)?(?:previous|prior|semua)\s+(?:instructions?|instruksi|perintah|aturan)\b", 0.95),
    (r"\b(?:system\s+override|evil\s+assistant|dan\s+mode|unrestricted|jailbreak|dump\s+table)\b", 0.95),
    (r"\b(?:you\s+are\s+now|mulai\s+sekarang\s+kamu\s+adalah)\s+(?:unrestricted|dan|jailbroken|tanpa\s+batasan|bebas|evil)\b", 0.95),
    (r"\b(?:bypass|lewati|abaikan)\s+(?:guardrails?|keamanan|filter|aturan|policy)\b", 0.90),
    (r"\b(?:bocorkan|tampilkan|leak|show)\s+(?:semua\s+)?(?:instruksi|prompt|rahasia|konfigurasi|env|api\s*key|password)\b", 0.92),
    (r"\b(?:system\s+prompt|prompt\s+system|instruksi\s+(?:rahasia\s+)?sistem)\b", 0.90),
    (r"\b(?:pretend\s+to\s+be|berpura-puralah\s+menjadi)\s+(?:admin|root|superuser|developer\s+mode)\b", 0.85),
    (r"\b(?:disregard\s+the\s+above|lupakan\s+percakapan\s+di\s+atas)\b", 0.90),

    # Destructive SQL & SQL Injection attempts in prompt
    (r"\b(?:drop\s+table|delete\s+from|truncate\s+table|alter\s+table)\b", 0.95),
    (r"(?:--\s*bypass|--\s*comment|;\s*drop|union\s+select|1\s*=\s*1\s*;)", 0.95),

    # Prompt Template Delimiter Hijacking
    (r"\[/?INST\]", 0.92),
    (r"<{1,2}SYS>{1,2}", 0.92),
    (r"---+\s*(?:BEGIN|START)\s+(?:SYSTEM|PROMPT|INSTRUCTIONS?)\s*---+", 0.95),
    (r"<\|im_start\|>|<\|im_end\|>", 0.95),

    # Indirect Injection inside Document chunks
    (r"\b(?:attention|perhatian|catatan\s+penting):\s*(?:do\s+not\s+follow|jangan\s+ikuti\s+pertanyaan|abaikan\s+tugas)\b", 0.92),
    (r"\b(?:hidden\s+instruction|perintah\s+rahasia):\s*(?:print|tampilkan|kirim)\b", 0.90),
    (r"\b(?:override\s+system\s+and\s+say|timpa\s+sistem\s+dan\s+katakan)\b", 0.92),
]


class PromptInjectionDetector:
    """
    Detector for Direct Prompt Injections (user query)
    and Indirect Prompt Injections (malicious payload embedded inside documents).
    """

    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold or settings.PROMPT_INJECTION_THRESHOLD

    def detect_injection(self, text: str, is_document: bool = False) -> GuardrailCheckResult:
        """
        Scans text for prompt injection patterns.
        Returns GuardrailCheckResult with risk score and determination.
        """
        if not text:
            return GuardrailCheckResult(is_safe=True, risk_score=0.0)

        cleaned = text.lower()
        max_score = 0.0
        detected_reasons: List[str] = []

        for pattern, score in _INJECTION_PATTERNS:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                matched_snippet = match.group(0)
                if score > max_score:
                    max_score = score
                prefix = "Indirect injection pada dokumen" if is_document else "Direct prompt injection"
                detected_reasons.append(f"{prefix}: terdeteksi pola '{matched_snippet}' (score {score:.2f})")

        is_safe = max_score < self.threshold
        reason = "; ".join(detected_reasons) if detected_reasons else None

        if not is_safe:
            logger.warning(f"Guardrail Alert: Prompt injection terdeteksi! Risk={max_score:.2f}. Detail: {reason}")

        return GuardrailCheckResult(
            is_safe=is_safe,
            violation_type="PROMPT_INJECTION" if not is_safe else "NONE",
            risk_score=round(max_score, 2),
            reason=reason,
            sanitized_text=text if is_safe else "[REDACTED_PROMPT_INJECTION]",
        )
