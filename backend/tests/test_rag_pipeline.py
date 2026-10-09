import os
import pytest
from app.rag.pipeline import RAGPipeline
from app.rag.embeddings import MultilingualSemanticEmbeddingService
from app.rag.vector_store import ChromaVectorStore


@pytest.fixture
def test_pipeline(tmp_path):
    temp_chroma_dir = str(tmp_path / "test_chroma")
    embed_svc = MultilingualSemanticEmbeddingService()
    vstore = ChromaVectorStore(
        collection_name="test_sop_collection",
        persist_directory=temp_chroma_dir,
        embedding_service=embed_svc,
    )
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/sop_docs"))
    pipeline = RAGPipeline(
        docs_dir=docs_dir,
        vector_store=vstore,
        embedding_service=embed_svc,
    )
    pipeline.ingest_directory(force_reindex=True)
    return pipeline


def test_rag_ingestion_stats(test_pipeline):
    stats = test_pipeline.vector_store.count()
    assert stats >= 4
    doc_names = test_pipeline.vector_store.get_document_names()
    assert any("SOP-OPS-001" in name for name in doc_names)
    assert any("SOP-OPS-002" in name for name in doc_names)
    assert any("SOP-PROC-003" in name for name in doc_names)
    assert any("SOP-FIN-004" in name for name in doc_names)


def test_rag_search_self_combustion_query(test_pipeline):
    # Query: self-combustion / temperature above 55 degrees
    query = "Bagaimana tindakan darurat jika suhu batubara di stockpile mencapai 55 C?"
    res = test_pipeline.search(query=query, top_k=2)
    
    assert res.total_results >= 1
    top_chunk = res.results[0].chunk
    assert top_chunk.doc_code == "SOP-OPS-002"
    assert top_chunk.page_number in [2, 3]
    # Verify content mentions hot coal or warning against spraying water
    assert ("MERAH" in top_chunk.content or "55" in top_chunk.content or "AIR" in top_chunk.content)
    # Check citation
    assert "SOP-OPS-002" in res.results[0].citation.citation_text
    assert "Halaman" in res.results[0].citation.citation_text


def test_rag_search_barge_weather_query(test_pipeline):
    # Query: barge loading and weather/rain
    query = "Kapan pemuatan batubara ke tongkang di jetty harus dihentikan saat cuaca hujan?"
    res = test_pipeline.search(query=query, top_k=2)
    
    assert res.total_results >= 1
    top_chunk = res.results[0].chunk
    assert top_chunk.doc_code == "SOP-OPS-001"
    assert "hujan" in top_chunk.content.lower() or "cuaca" in top_chunk.content.lower()
    assert "Halaman 2" in res.results[0].citation.citation_text


def test_rag_search_po_approval_query(test_pipeline):
    # Query: PO approval rules
    query = "Apakah staff boleh menyetujui Purchase Order batubara?"
    res = test_pipeline.search(query=query, top_k=2)
    
    assert res.total_results >= 1
    top_chunk = res.results[0].chunk
    assert top_chunk.doc_code == "SOP-PROC-003"
    assert "draft" in top_chunk.content.lower()
    assert "manager" in top_chunk.content.lower()
