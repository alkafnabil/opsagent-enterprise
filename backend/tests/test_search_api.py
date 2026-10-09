from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_index_docs_endpoint():
    response = client.post("/api/v1/index-docs?force_reindex=true")
    assert response.status_code == 200
    data = response.json()
    assert data["total_documents"] >= 4
    assert data["total_chunks"] >= 4
    assert len(data["documents"]) >= 4


def test_get_index_stats_endpoint():
    response = client.get("/api/v1/index-docs/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_documents"] >= 4
    assert data["total_chunks"] >= 4


def test_search_docs_post_endpoint():
    payload = {
        "query": "Berapa batas toleransi selisih timbangan pada tagihan invoice customer?",
        "top_k": 2,
    }
    response = client.post("/api/v1/search-docs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] >= 1
    assert "results" in data
    assert "formatted_context" in data
    assert "citations" in data
    assert len(data["citations"]) >= 1
    
    top = data["results"][0]
    assert "chunk" in top
    assert "citation" in top
    assert top["chunk"]["doc_code"] == "SOP-FIN-004"
    assert "Halaman 3" in top["citation"]["citation_text"]


def test_search_docs_get_endpoint():
    response = client.get("/api/v1/search-docs?q=kebakaran+batubara+suhu+55&top_k=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] >= 1
    assert any("SOP-OPS-002" in c for c in data["citations"])
