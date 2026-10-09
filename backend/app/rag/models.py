from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk identifier, e.g. SOP-OPS-001-P2-C01")
    doc_file_name: str = Field(..., description="File name, e.g. SOP-OPS-001_Bongkar_Muat_Tongkang_Jetty.md")
    doc_code: str = Field(..., description="Document code, e.g. SOP-OPS-001")
    doc_title: str = Field(..., description="Document title")
    page_number: int = Field(..., ge=1, description="Page number where this chunk originates")
    section_title: str = Field(..., description="Section / Chapter header, e.g. 4. PELAKSANAAN PEMUATAN")
    content: str = Field(..., description="The chunk text content")
    token_count: int = Field(..., ge=1, description="Number of tokens in this chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional custom metadata")


class Citation(BaseModel):
    source: str = Field(..., description="Source document name / code")
    page: int = Field(..., ge=1, description="Page number")
    section: str = Field(..., description="Section title")
    citation_text: str = Field(..., description="Formatted citation label, e.g. [SOP-OPS-001: Halaman 2, Bagian 4]")


class SearchResult(BaseModel):
    chunk: DocumentChunk
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    citation: Citation


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="User search query in Indonesian")
    top_k: int = Field(3, ge=1, le=10, description="Number of relevant chunks to retrieve")
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score")
    doc_filter: Optional[str] = Field(None, description="Filter by doc code, e.g. 'SOP-OPS-001'")


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    formatted_context: str = Field(..., description="Clean formatted context for LLM synthesis")
    citations: List[str] = Field(..., description="List of unique citations used")


class IndexStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    documents: List[str]
    vector_store_type: str
    embedding_model: str
