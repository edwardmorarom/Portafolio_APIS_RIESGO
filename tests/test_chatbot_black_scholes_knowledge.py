from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.chatbot_knowledge import CHATBOT_KNOWLEDGE_BASE  # noqa: E402
from app.services.chatbot_service import ChatbotService  # noqa: E402


def test_chatbot_knowledge_contains_black_scholes():
    assert "black_scholes" in CHATBOT_KNOWLEDGE_BASE

    payload = CHATBOT_KNOWLEDGE_BASE["black_scholes"]

    assert "call" in payload["keywords"]
    assert "put" in payload["keywords"]
    assert "griegas" in payload["keywords"]


def test_chatbot_black_scholes_general_answer_mentions_option_inputs():
    service = ChatbotService()

    result = service.answer_question(
        question="Explicame Black-Scholes para opciones",
        mode="general",
        module="black_scholes",
    )

    assert result["supported"] is True
    assert "call" in result["answer"]
    assert "put" in result["answer"]
    assert "strike" in result["answer"]
    assert "volatilidad" in result["answer"]


def test_chatbot_black_scholes_statistical_answer_mentions_greeks():
    service = ChatbotService()

    result = service.answer_question(
        question="Que son las griegas en Black-Scholes?",
        mode="estadistico",
        module="black_scholes",
    )

    assert result["supported"] is True
    assert "delta" in result["answer"]
    assert "gamma" in result["answer"]
    assert "vega" in result["answer"]
    assert "theta" in result["answer"]
    assert "rho" in result["answer"]
