from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_backend_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "opsagent_backend"
    assert "llm_provider" in data
    assert "router_model" in data
    assert "synthesis_model" in data


def test_backend_settings_defaults():
    assert settings.BACKEND_PORT == 8000
    assert settings.MOCK_ERP_PORT == 8001
    assert settings.GUARDRAILS_ENABLED is True
    assert settings.CHUNK_SIZE_TOKENS >= 500
    assert settings.CHUNK_OVERLAP_TOKENS == 80
