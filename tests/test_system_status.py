from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_system_status_endpoint():
    response = client.get("/api/v1/system/status")

    assert response.status_code == 200

    data = response.json()

    assert data["app_name"]
    assert data["app_version"]
    assert "environment" in data
    assert "database_configured" in data
    assert "ml_enabled" in data
    assert "chatbot_provider" in data
