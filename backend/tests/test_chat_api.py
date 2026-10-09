from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_streaming_endpoint():
    payload = {
        "query": "Berapa stok batubara di Stockpile Palaran?",
        "user_role": "staff",
        "user_id": "USR-DIMAS",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    
    content = response.text
    assert "event: trace_init" in content
    assert "event: router_step" in content
    assert "event: done" in content


def test_chat_sync_endpoint():
    payload = {
        "query": "Cek jadwal rapat koordinasi loading tongkang",
        "user_role": "staff",
        "user_id": "USR-DIMAS",
    }
    response = client.post("/api/v1/chat/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "trace_id" in data
    assert data["routed_intent"] == "m365"
    assert "final_answer" in data
    assert len(data["final_answer"]) > 10


def test_get_audit_logs_endpoint():
    response = client.get("/api/v1/audit-logs?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "logs" in data
