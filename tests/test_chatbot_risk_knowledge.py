from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.chatbot_knowledge import CHATBOT_KNOWLEDGE_BASE  # noqa: E402
from app.services.chatbot_service import ChatbotService  # noqa: E402


def test_chatbot_knowledge_contains_var_cvar_and_kupiec():
    assert "var" in CHATBOT_KNOWLEDGE_BASE
    assert "cvar" in CHATBOT_KNOWLEDGE_BASE
    assert "kupiec" in CHATBOT_KNOWLEDGE_BASE


def test_chatbot_var_answer_mentions_three_methods():
    service = ChatbotService()

    result = service.answer_question(
        question="Explicame el VaR del portafolio",
        mode="general",
        module="var",
    )

    assert result["supported"] is True
    assert "parametrico" in result["answer"]
    assert "historico" in result["answer"]
    assert "Monte Carlo" in result["answer"]


def test_chatbot_cvar_answer_mentions_tail_risk():
    service = ChatbotService()

    result = service.answer_question(
        question="Que es el CVaR o expected shortfall",
        mode="estadistico",
        module="cvar",
    )

    assert result["supported"] is True
    assert "cola" in result["answer"]


def test_chatbot_kupiec_answer_is_supported():
    service = ChatbotService()

    result = service.answer_question(
        question="Como funciona el backtesting de Kupiec",
        mode="estadistico",
        module="kupiec",
    )

    assert result["supported"] is True
    assert "LR_POF" in result["answer"]
    assert "chi-cuadrado" in result["answer"]
