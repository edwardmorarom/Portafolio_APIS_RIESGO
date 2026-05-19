from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.chatbot_knowledge import CHATBOT_KNOWLEDGE_BASE  # noqa: E402
from app.services.chatbot_service import ChatbotService  # noqa: E402


def test_chatbot_knowledge_contains_kyc_and_roboadvisor():
    assert "kyc" in CHATBOT_KNOWLEDGE_BASE
    assert "roboadvisor" in CHATBOT_KNOWLEDGE_BASE


def test_chatbot_kyc_answer_mentions_profiles_and_horizon():
    service = ChatbotService()

    result = service.answer_question(
        question="Explicame KYC y perfil de riesgo",
        mode="general",
        module="kyc",
    )

    assert result["supported"] is True
    assert "conservador" in result["answer"]
    assert "moderado" in result["answer"]
    assert "agresivo" in result["answer"]
    assert "horizonte" in result["answer"]


def test_chatbot_kyc_statistical_answer_mentions_risk_metrics():
    service = ChatbotService()

    result = service.answer_question(
        question="Como se conecta el KYC con las metricas de riesgo?",
        mode="estadistico",
        module="kyc",
    )

    assert result["supported"] is True
    assert "VaR" in result["answer"]
    assert "CVaR" in result["answer"]
    assert "drawdown" in result["answer"]


def test_chatbot_roboadvisor_answer_mentions_automated_portfolio():
    service = ChatbotService()

    result = service.answer_question(
        question="Que es el RoboAdvisor del proyecto?",
        mode="general",
        module="roboadvisor",
    )

    assert result["supported"] is True
    assert "portafolios" in result["answer"]
    assert "automatizada" in result["answer"]
    assert "conservador" in result["answer"]


def test_chatbot_roboadvisor_statistical_answer_mentions_metrics():
    service = ChatbotService()

    result = service.answer_question(
        question="Como se valida una recomendacion del RoboAdvisor?",
        mode="estadistico",
        module="roboadvisor",
    )

    assert result["supported"] is True
    assert "Sharpe" in result["answer"]
    assert "VaR" in result["answer"]
    assert "CVaR" in result["answer"]
