from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402
from app.core.chatbot_scope import is_financial_question  # noqa: E402


def test_chatbot_rejects_non_financial_question():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chatbot/ask",
            json={
                "question": "Dame una receta de cocina con pollo",
                "mode": "general",
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["supported"] is False
    assert payload["topics"] == []
    assert "fuera del alcance financiero" in payload["answer"]


def test_chatbot_accepts_financial_question_by_keyword():
    assert is_financial_question("Explícame el riesgo de un portafolio") is True


def test_chatbot_accepts_financial_question_by_module():
    assert is_financial_question("Explícame esto", module="var") is True


def test_chatbot_rejects_non_financial_scope_helper():
    assert is_financial_question("Cuál es la mejor receta de pasta") is False
