from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.chatbot_knowledge import CHATBOT_KNOWLEDGE_BASE  # noqa: E402
from app.services.chatbot_service import ChatbotService  # noqa: E402


def test_chatbot_knowledge_contains_garch():
    assert "garch" in CHATBOT_KNOWLEDGE_BASE

    payload = CHATBOT_KNOWLEDGE_BASE["garch"]

    assert "arch" in payload["keywords"]
    assert "egarch" in payload["keywords"]
    assert "volatilidad condicional" in payload["keywords"]


def test_chatbot_garch_general_answer_mentions_arch_garch_egarch():
    service = ChatbotService()

    result = service.answer_question(
        question="Explicame GARCH y volatilidad condicional",
        mode="general",
        module="garch",
    )

    assert result["supported"] is True
    assert "ARCH" in result["answer"]
    assert "GARCH" in result["answer"]
    assert "EGARCH" in result["answer"]


def test_chatbot_garch_statistical_answer_mentions_aic_bic_and_residuals():
    service = ChatbotService()

    result = service.answer_question(
        question="Como se selecciona un modelo GARCH?",
        mode="estadistico",
        module="garch",
    )

    assert result["supported"] is True
    assert "AIC" in result["answer"]
    assert "BIC" in result["answer"]
    assert "residuos" in result["answer"]

