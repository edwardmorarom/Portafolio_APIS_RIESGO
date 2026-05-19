from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.chatbot_knowledge import CHATBOT_KNOWLEDGE_BASE  # noqa: E402
from app.services.chatbot_service import ChatbotService  # noqa: E402


def test_chatbot_knowledge_contains_capm():
    assert "capm" in CHATBOT_KNOWLEDGE_BASE

    payload = CHATBOT_KNOWLEDGE_BASE["capm"]

    assert "beta" in payload["keywords"]
    assert "alpha" in payload["keywords"]
    assert "retorno esperado" in payload["keywords"]


def test_chatbot_capm_general_answer_mentions_beta_and_alpha():
    service = ChatbotService()

    result = service.answer_question(
        question="Explicame CAPM, beta y alpha",
        mode="general",
        module="capm",
    )

    assert result["supported"] is True
    assert "beta" in result["answer"]
    assert "alpha" in result["answer"]
    assert "benchmark" in result["answer"]


def test_chatbot_capm_statistical_answer_mentions_covariance_and_r2():
    service = ChatbotService()

    result = service.answer_question(
        question="Como se calcula beta en CAPM?",
        mode="estadistico",
        module="capm",
    )

    assert result["supported"] is True
    assert "covarianza" in result["answer"]
    assert "varianza" in result["answer"]
    assert "R2" in result["answer"]


def test_chatbot_capm_detects_topic_without_module():
    service = ChatbotService()

    result = service.answer_question(
        question="Que significa una beta mayor que 1 frente al mercado?",
        mode="general",
    )

    assert result["supported"] is True
    assert "capm" in result["topics"]
