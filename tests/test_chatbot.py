from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402
from app.services.chatbot_service import ChatbotService  # noqa: E402


class _KycOnlyLLM:
    def generate_answer(self, question: str, context: str, mode: str) -> str:
        return "El KYC define el perfil del inversionista y su tolerancia al riesgo."


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
                "question": "Dame una receta de cocina",
                "mode": "general",
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["supported"] is False
    assert payload["topics"] == []
    assert "fuera del alcance financiero" in payload["answer"]


def test_chatbot_uses_portfolio_context_and_question_text():
    with TestClient(app) as client:
        response_portfolio = client.post(
            "/api/v1/chatbot/ask",
            json={
                "question": "¿Cómo explico el VaR de mi portafolio actual?",
                "mode": "general",
                "module": "var",
                "portfolio_context": {
                    "tickers": ["AAPL", "MSFT"],
                    "weights_pct": [60, 40],
                    "horizon": "1y",
                    "benchmark": {"ticker": "SPY"},
                },
            },
        )
        response_concept = client.post(
            "/api/v1/chatbot/ask",
            json={
                "question": "¿Qué es VaR?",
                "mode": "general",
                "module": "var",
            },
        )

    assert response_portfolio.status_code == 200
    assert response_concept.status_code == 200
    answer_portfolio = response_portfolio.json()["answer"]
    answer_concept = response_concept.json()["answer"]

    assert "AAPL" in answer_portfolio
    assert "SPY" in answer_portfolio
    assert answer_portfolio != answer_concept


def test_chatbot_ml_question_is_supported():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chatbot/ask",
            json={
                "question": "¿Qué hace el módulo de Machine Learning?",
                "mode": "general",
                "module": "ml",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["supported"] is True
    assert payload["answer"]


def test_chatbot_general_dashboard_and_horizon_questions_are_contextual():
    with TestClient(app) as client:
        response_dashboard = client.post(
            "/api/v1/chatbot/ask",
            json={"question": "¿Qué hace este dashboard?", "mode": "general"},
        )
        response_horizon = client.post(
            "/api/v1/chatbot/ask",
            json={"question": "¿Cómo afecta el horizonte al riesgo?", "mode": "general"},
        )

    assert response_dashboard.status_code == 200
    assert response_horizon.status_code == 200
    answer_dashboard = response_dashboard.json()["answer"].lower()
    answer_horizon = response_horizon.json()["answer"].lower()
    assert "dashboard" in answer_dashboard or "portafolio" in answer_dashboard
    assert "horizonte" in answer_horizon
    assert answer_dashboard != answer_horizon


def test_chatbot_discards_misaligned_kyc_llm_answer_for_var():
    service = ChatbotService(llm_client=_KycOnlyLLM())

    payload = service.answer_question(
        question="Explícame el VaR del portafolio",
        mode="general",
        module="var",
    )

    assert payload["supported"] is True
    assert "VaR" in payload["answer"] or "var" in payload["answer"].lower()
    assert "KYC define" not in payload["answer"]
