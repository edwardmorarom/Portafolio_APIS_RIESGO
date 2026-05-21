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
