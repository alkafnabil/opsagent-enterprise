from __future__ import annotations
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.tools.base import BaseTool
from app.rag.pipeline import get_rag_pipeline

logger = logging.getLogger(__name__)


class SearchDocsInput(BaseModel):
    query: str = Field(
        ...,
        description="Pertanyaan atau topik pencarian SOP internal (contoh: 'aturan pemuatan saat hujan lebat' atau 'tindakan suhu batubara > 55 C')",
    )
    top_k: Optional[int] = Field(3, ge=1, le=5, description="Jumlah potongan dokumen relevan yang diambil")
    doc_filter: Optional[str] = Field(None, description="Kode SOP spesifik jika ingin difilter (e.g. 'SOP-OPS-001')")


class SearchDocsTool(BaseTool):
    name: str = "search_docs"
    description: str = (
        "Pencarian RAG semantik atas Standar Operasional Prosedur (SOP) internal batubara. "
        "Mengembalikan konteks aturan resmi, penanganan insiden, batas toleransi, dan nomor halaman sitasi."
    )
    args_schema: type[BaseModel] = SearchDocsInput
    timeout_seconds: float = 8.0
    max_retries: int = 1

    async def _run(self, args: SearchDocsInput) -> Dict[str, Any]:
        pipeline = get_rag_pipeline()
        response = pipeline.search(
            query=args.query,
            top_k=args.top_k or 3,
            doc_filter=args.doc_filter,
        )
        return {
            "query": response.query,
            "total_found": response.total_results,
            "citations": response.citations,
            "formatted_context": response.formatted_context,
            "chunks": [
                {
                    "doc_code": r.chunk.doc_code,
                    "doc_file_name": r.chunk.doc_file_name,
                    "page_number": r.chunk.page_number,
                    "section_title": r.chunk.section_title,
                    "similarity_score": r.similarity_score,
                    "content": r.chunk.content,
                    "citation_text": r.citation.citation_text,
                }
                for r in response.results
            ],
        }

    def _summarize_output(self, output: Any) -> str:
        if isinstance(output, dict):
            citations = output.get("citations", [])
            cit_str = ", ".join(citations[:2]) if citations else "tidak ada"
            return f"Ditemukan {output.get('total_found', 0)} kutipan SOP ({cit_str})."
        return super()._summarize_output(output)
