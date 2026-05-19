from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.chatbot_knowledge import CHATBOT_KNOWLEDGE_BASE  # noqa: E402
from app.services.chatbot_service import ChatbotService  # noqa: E402


def test_chatbot_knowledge_contains_nelson_siegel():
    assert "nelson_siegel" in CHATBOT_KNOWLEDGE_BASE

    payload = CHATBOT_KNOWLEDGE_BASE["nelson_siegel"]

    assert "beta0" in payload["keywords"]
    assert "beta1" in payload["keywords"]
    assert "beta2" in payload["keywords"]
    assert "tau" in payload["keywords"]


def test_chatbot_nelson_siegel_general_answer_mentions_curve_components():
    service = ChatbotService()

    result = service.answer_question(
        question="Explicame Nelson-Siegel y la curva de tasas",
        mode="general",
        module="nelson_siegel",
    )

    assert result["supported"] is True
    assert "curva de tasas" in result["answer"]
    assert "nivel" in result["answer"]
    assert "pendiente" in result["answer"]
    assert "curvatura" in result["answer"]


def test_chatbot_nelson_siegel_statistical_answer_mentions_parameters():
    service = ChatbotService()

    result = service.answer_question(
        question="Que significan beta0 beta1 beta2 y tau en Nelson-Siegel?",
        mode="estadistico",
        module="nelson_siegel",
    )

    assert result["supported"] is True
    assert "beta0" in result["answer"]
    assert "beta1" in result["answer"]
    assert "beta2" in result["answer"]
    assert "tau" in result["answer"]
