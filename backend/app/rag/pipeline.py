from __future__ import annotations
import os
import glob
import logging
from typing import List, Optional
from app.core.config import settings
from .models import (
    DocumentChunk,
    SearchResult,
    SearchRequest,
    SearchResponse,
    IndexStatsResponse,
)
from .chunker import RecursiveTokenChunker
from .embeddings import get_embedding_service, BaseEmbeddingService
from .vector_store import get_vector_store, BaseVectorStore

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    End-to-end RAG Pipeline for OpsAgent.
    Handles SOP ingestion, 500-800 token chunking, 80-token overlap,
    vector store indexing, and semantic search with structured citations.
    """

    def __init__(
        self,
        docs_dir: Optional[str] = None,
        chunker: Optional[RecursiveTokenChunker] = None,
        vector_store: Optional[BaseVectorStore] = None,
        embedding_service: Optional[BaseEmbeddingService] = None,
    ):
        self.docs_dir = docs_dir or os.path.join(os.path.dirname(__file__), "../../../data/sop_docs")
        self.docs_dir = os.path.abspath(self.docs_dir)
        self.chunker = chunker or RecursiveTokenChunker(
            target_min_tokens=settings.CHUNK_SIZE_TOKENS - 150,
            target_max_tokens=settings.CHUNK_SIZE_TOKENS + 150,
            overlap_tokens=settings.CHUNK_OVERLAP_TOKENS,
        )
        self.embedding_service = embedding_service or get_embedding_service()
        self.vector_store = vector_store or get_vector_store(self.embedding_service)

    def ingest_directory(self, force_reindex: bool = False) -> IndexStatsResponse:
        """
        Reads all Markdown SOP files from docs_dir, chunks them, and indexes into vector store.
        """
        if force_reindex:
            self.vector_store.clear()

        pattern = os.path.join(self.docs_dir, "*.md")
        files = glob.glob(pattern)

        if not files:
            logger.warning(f"Tidak ada file SOP (.md) ditemukan di {self.docs_dir}")
            return IndexStatsResponse(
                total_documents=0,
                total_chunks=self.vector_store.count(),
                documents=[],
                vector_store_type=settings.VECTOR_STORE_TYPE,
                embedding_model=settings.EMBEDDING_MODEL,
            )

        all_chunks: List[DocumentChunk] = []
        indexed_files: List[str] = []

        for file_path in files:
            file_name = os.path.basename(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = self.chunker.chunk_document(content, file_name)
            all_chunks.extend(chunks)
            indexed_files.append(file_name)
            logger.info(f"Ingested {file_name}: {len(chunks)} chunks.")

        self.vector_store.add_chunks(all_chunks)

        return IndexStatsResponse(
            total_documents=len(indexed_files),
            total_chunks=self.vector_store.count(),
            documents=indexed_files,
            vector_store_type=settings.VECTOR_STORE_TYPE,
            embedding_model=settings.EMBEDDING_MODEL,
        )

    def format_context_for_llm(self, results: List[SearchResult]) -> str:
        """
        Constructs context text formatted with explicit citations for the synthesis model.
        Format required: Document name, page number, and section header.
        """
        if not results:
            return "Tidak ada dokumen SOP yang relevan dengan pertanyaan ini."

        context_blocks = []
        for i, res in enumerate(results, 1):
            chunk = res.chunk
            header = (
                f"--- [DOKUMEN: {chunk.doc_file_name} | KODE: {chunk.doc_code} | "
                f"HALAMAN: {chunk.page_number} | BAGIAN: {chunk.section_title}] ---"
            )
            context_blocks.append(f"{header}\n{chunk.content}\n")

        return "\n".join(context_blocks)

    def search(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: Optional[float] = None,
        doc_filter: Optional[str] = None,
    ) -> SearchResponse:
        """
        Executes semantic search over SOP documents and constructs response with citations.
        Auto-ingests if vector store is empty.
        """
        if self.vector_store.count() == 0:
            logger.info("Vector store kosong, menjalankan auto-ingestion...")
            self.ingest_directory()

        results = self.vector_store.search(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            doc_filter=doc_filter,
        )

        formatted_context = self.format_context_for_llm(results)
        unique_citations = list(dict.fromkeys(r.citation.citation_text for r in results))

        return SearchResponse(
            query=query,
            results=results,
            total_results=len(results),
            formatted_context=formatted_context,
            citations=unique_citations,
        )


_default_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    global _default_pipeline
    if _default_pipeline is None:
        _default_pipeline = RAGPipeline()
    return _default_pipeline
