from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status
from app.rag.models import (
    SearchRequest,
    SearchResponse,
    IndexStatsResponse,
)
from app.rag.pipeline import get_rag_pipeline

router = APIRouter(prefix="/v1", tags=["RAG & SOP Search"])


@router.post("/search-docs", response_model=SearchResponse)
async def search_documents_post(req: SearchRequest):
    """
    Search operational SOP documents via semantic vector search.
    Returns matched chunks along with explicit source document and page number citations.
    """
    pipeline = get_rag_pipeline()
    try:
        response = pipeline.search(
            query=req.query,
            top_k=req.top_k,
            score_threshold=req.score_threshold,
            doc_filter=req.doc_filter,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan saat pencarian dokumen RAG: {str(e)}",
        )


@router.get("/search-docs", response_model=SearchResponse)
async def search_documents_get(
    q: str = Query(..., min_length=2, description="Search query in Indonesian"),
    top_k: int = Query(3, ge=1, le=10, description="Number of results to return"),
    doc_filter: Optional[str] = Query(None, description="Optional doc code filter"),
):
    """GET endpoint for searching operational SOP documents."""
    pipeline = get_rag_pipeline()
    try:
        response = pipeline.search(
            query=q,
            top_k=top_k,
            doc_filter=doc_filter,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan saat pencarian dokumen RAG: {str(e)}",
        )


@router.post("/index-docs", response_model=IndexStatsResponse)
async def trigger_reindex(force_reindex: bool = Query(False, description="Clear and reindex all docs")):
    """
    Triggers indexing of SOP documents from data/sop_docs into vector store.
    """
    pipeline = get_rag_pipeline()
    try:
        stats = pipeline.ingest_directory(force_reindex=force_reindex)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal melakukan indexing dokumen: {str(e)}",
        )


@router.get("/index-docs/stats", response_model=IndexStatsResponse)
async def get_index_stats():
    """Retrieve current vector store indexing stats."""
    pipeline = get_rag_pipeline()
    docs = pipeline.vector_store.get_document_names()
    return IndexStatsResponse(
        total_documents=len(docs),
        total_chunks=pipeline.vector_store.count(),
        documents=docs,
        vector_store_type=pipeline.vector_store.__class__.__name__,
        embedding_model=pipeline.embedding_service.__class__.__name__,
    )
