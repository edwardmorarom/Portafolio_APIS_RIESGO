from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


def test_chatbot_answers_supported_var_question():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chatbot/ask",
            json={
                "question": "¿Qué es el VaR y cómo se interpreta?",
                "mode": "general",
                "module": "var",
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["supported"] is True
    assert payload["module"] == "var"
    assert "var" in payload["topics"]
    assert payload["answer"]
    assert payload["sources"]


def test_chatbot_returns_controlled_response_for_financial_but_unsupported_question():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chatbot/ask",
            json={
                "question": "Explícame la duración modificada de bonos",
                "mode": "general",
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["supported"] is False
    assert payload["topics"] == []
    assert "No encontré soporte suficiente" in payload["answer"]
