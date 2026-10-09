from __future__ import annotations
import time
from typing import Tuple
from app.agent.llm_provider import LLMProvider


class IntentRouter:
    """
    Two-Tier Architecture Router.
    Uses small fast model to classify query intent and select corresponding tool.
    Measures latency per step (< 250 ms).
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def route_query(self, user_query: str) -> Tuple[str, float, float]:
        """
        Returns (intent, confidence, latency_ms).
        Intents: 'sql_query', 'erp_api', 'm365', 'search_docs', 'out_of_scope'.
        """
        start = time.perf_counter()
        intent, confidence = await self.llm_provider.call_router(user_query)
        latency_ms = (time.perf_counter() - start) * 1000.0
        return intent, confidence, round(latency_ms, 2)
