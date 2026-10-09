from __future__ import annotations
import json
import logging
from typing import List, Dict, Any, Optional, AsyncIterator, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider:
    """
    Unified LLM Provider abstraction supporting:
    - Groq (Llama-3.1-8B-instant, Llama-3.3-70b-versatile)
    - OpenAI (GPT-4o, GPT-4o-mini)
    - Anthropic (Claude-3.5-Sonnet)
    - Deterministic Local Engine (Test runner & offline environment fallback)
    """

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.DEFAULT_LLM_PROVIDER

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Estimate cost in USD based on model pricing."""
        if "8b" in model.lower():
            # Groq Llama 3.1 8B: $0.05 / 1M prompt, $0.08 / 1M completion
            return (prompt_tokens * 0.05 + completion_tokens * 0.08) / 1_000_000.0
        elif "70b" in model.lower():
            # Groq Llama 3.3 70B: $0.59 / 1M prompt, $0.79 / 1M completion
            return (prompt_tokens * 0.59 + completion_tokens * 0.79) / 1_000_000.0
        elif "gpt-4o-mini" in model.lower():
            return (prompt_tokens * 0.15 + completion_tokens * 0.60) / 1_000_000.0
        elif "gpt-4o" in model.lower():
            return (prompt_tokens * 2.50 + completion_tokens * 10.00) / 1_000_000.0
        else:
            return (prompt_tokens * 0.10 + completion_tokens * 0.20) / 1_000_000.0

    async def call_router(self, user_query: str) -> Tuple[str, float]:
        """
        Fast intent classification using the small Router model (or fast domain heuristics).
        Returns (intent, confidence_score).
        """
        # If real Groq/OpenAI key is available, call the API
        if self._has_valid_api_key():
            try:
                return await self._call_remote_router(user_query)
            except Exception as e:
                logger.warning(f"Remote router API failed ({e}), using local deterministic router.")

        return self._local_heuristic_router(user_query)

    def _has_valid_api_key(self) -> bool:
        if self.provider == "groq":
            return bool(settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("mock_") and len(settings.GROQ_API_KEY) > 15)
        elif self.provider == "openai":
            return bool(settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("mock_") and len(settings.OPENAI_API_KEY) > 15)
        elif self.provider == "anthropic":
            return bool(settings.ANTHROPIC_API_KEY and not settings.ANTHROPIC_API_KEY.startswith("mock_") and len(settings.ANTHROPIC_API_KEY) > 15)
        return False

    async def _call_remote_router(self, query: str) -> Tuple[str, float]:
        system_prompt = (
            "Klasifikasikan intent pengguna ke dalam SALAH SATU label berikut:\n"
            "- sql_query: pertanyaan data operasional batubara (stok batubara, pergerakan tongkang/kapal/barge, status/jadwal berlayar tongkang, tracking shipment ke PLTU, produksi pit tambang, nama supplier/customer)\n"
            "- erp_api: inquiry tagihan/invoice overdue, pengecekan pembayaran, evaluasi kuota kontrak supplier, atau pembuatan draft Purchase Order (PO)\n"
            "- m365: jadwal rapat internal/meeting koordinasi jetty, kalender kosong, atau draft memo/email\n"
            "- search_docs: SOP operasional, penanganan kebakaran batubara/self-combustion, prosedur cuaca hujan/angin kencang, batas toleransi timbangan\n"
            "- out_of_scope: topik umum di luar urusan operasional perusahaan (resep, zodiak, politik, dsb)\n\n"
            "PENTING: Status dan jadwal pengiriman tongkang/barge batubara ke PLTU selalu masuk ke sql_query.\n"
            "Jawab HANYA dalam format JSON valid: {\"intent\": \"...\", \"confidence\": 0.95}"
        )
        if self.provider == "groq":
            from groq import AsyncGroq
            client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            resp = await client.chat.completions.create(
                model=settings.ROUTER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content)
            return data.get("intent", "sql_query"), float(data.get("confidence", 0.95))

        elif self.provider == "openai":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content)
            return data.get("intent", "sql_query"), float(data.get("confidence", 0.95))

        return self._local_heuristic_router(query)

    def _local_heuristic_router(self, query: str) -> Tuple[str, float]:
        """Deterministic, zero-latency classifier with high domain fidelity."""
        q = query.lower()

        # 1. Out-of-scope check
        out_keywords = [
            "resep", "zodiak", "ramalan", "politik", "presiden", "film",
            "sepak bola", "puisi", "lelucon", "wisata", "chord", "lirik",
            "cuaca tokyo", "hotel", "game", "masakan", "tokyo"
        ]
        if any(w in q for w in out_keywords):
            return "out_of_scope", 0.98

        # 2. SOP, RAG & Policy check (SOP-001, SOP-002, SOP-003, SOP-004)
        sop_keywords = [
            "sop", "prosedur", "tindakan standar", "hotspot", "mengeluarkan asap",
            "draft survey", "tahapan", "cuaca buruk", "wajib dihentikan",
            "kecepatan angin", "ship loader", "berwenang", "kewenangan",
            "berhak menandatangani", "tanda tangan kontrak", "batas toleransi",
            "toleransi timbangan", "selisih timbangan", "debit credit note",
            "syarat dokumen", "berita acara", "self-combustion", "kebakaran",
            "suhunya mencapai 55", "suhu mencapai 55", "panas batubara"
        ]
        if any(w in q for w in sop_keywords):
            return "search_docs", 0.96

        # 3. M365 check (Email & Meeting scheduling - exclude barge logistics)
        is_barge_or_stock = any(k in q for k in ["tongkang", "barge", "kapal", "stok", "stockpile", "pltu", "suralaya", "pengiriman"])
        m365_keywords = ["rapat", "kalender", "meeting", "email", "draft email", "kirim email", "agenda rapat", "slot kosong"]
        if any(w in q for w in m365_keywords) or ("jadwal" in q and not is_barge_or_stock):
            return "m365", 0.95

        # 4. ERP check (Invoices, PO, Suppliers, Contracts)
        erp_keywords = [
            "buat po", "create po", "draft po", "draf po", "purchase order", "order pembelian",
            "invoice", "tagihan", "overdue", "jatuh tempo", "faktur", "piutang",
            "evaluasi supplier", "kuota supplier", "kuota tambang", "kuota kontrak"
        ]
        if any(w in q for w in erp_keywords):
            return "erp_api", 0.95

        # 5. Default operational inquiry -> sql_query (Stockpiles, Shipments, Production, Customers)
        return "sql_query", 0.94

    async def stream_synthesis(
        self,
        user_query: str,
        tool_results_summary: str,
        citations: List[str],
        user_role: str = "staff",
    ) -> AsyncIterator[str]:
        """
        Stream synthesized response tokens in Indonesian.
        Combines tool outputs and citations into a clear, professional answer.
        """
        # If remote synthesis model is configured
        if self._has_valid_api_key():
            try:
                async for token in self._remote_stream_synthesis(user_query, tool_results_summary, citations, user_role):
                    yield token
                return
            except Exception as e:
                logger.warning(f"Remote synthesis failed ({e}), using local synthesis generator.")

        # Local deterministic synthesis streaming
        async for token in self._local_stream_synthesis(user_query, tool_results_summary, citations):
            yield token

    async def _remote_stream_synthesis(
        self,
        user_query: str,
        tool_results_summary: str,
        citations: List[str],
        user_role: str,
    ) -> AsyncIterator[str]:
        cit_block = "\n".join(f"- {c}" for c in citations) if citations else "Tidak ada dokumen SOP yang dikutip."
        system_msg = (
            "Anda adalah OpsAgent, asisten AI operasional internal PT Nusantara Coal Operations. "
            "Jawablah pertanyaan karyawan secara santun, presisi, dan berbasis data faktual dari tool trace yang diberikan. "
            "Sertakan sitasi sumber dengan format [Nama Dokumen: Halaman X, Bagian Y] jika mengambil dari SOP. "
            "Jika ada data yang membutuhkan persetujuan manager, sampaikan dengan jelas."
        )
        user_msg = (
            f"Pertanyaan Karyawan: {user_query}\n"
            f"Peran Pengguna: {user_role}\n\n"
            f"Hasil Eksekusi Tool Trace:\n{tool_results_summary}\n\n"
            f"Sitasi Tersedia:\n{cit_block}\n\n"
            f"Berikan jawaban lengkap dalam Bahasa Indonesia."
        )

        if self.provider == "groq":
            from groq import AsyncGroq
            client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            stream = await client.chat.completions.create(
                model=settings.SYNTHESIS_MODEL,
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
                temperature=0.2,
                stream=True,
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield content

        elif self.provider == "openai":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            stream = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
                temperature=0.2,
                stream=True,
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield content

    async def _local_stream_synthesis(
        self,
        user_query: str,
        tool_results_summary: str,
        citations: List[str],
    ) -> AsyncIterator[str]:
        import asyncio

        # Synthesize clear Indonesian operational answer
        response_text = f"Berdasarkan data operasional internal PT Nusantara Coal Operations:\n\n"
        response_text += f"{tool_results_summary}\n\n"
        
        if citations:
            response_text += "**Referensi & Sitasi SOP Resmi:**\n"
            for cit in citations:
                response_text += f"- {cit}\n"
            response_text += "\n"

        response_text += "Harap koordinasikan dengan Loading Master atau Supervisor terkait apabila membutuhkan penyesuaian di lapangan."

        # Stream words with small realistic delay
        words = response_text.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield token
            await asyncio.sleep(0.015)
