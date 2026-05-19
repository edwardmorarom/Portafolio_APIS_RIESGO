from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.chatbot_knowledge import CHATBOT_KNOWLEDGE_BASE  # noqa: E402
from app.services.chatbot_service import ChatbotService  # noqa: E402


def test_chatbot_knowledge_contains_markowitz_and_perri():
    assert "markowitz" in CHATBOT_KNOWLEDGE_BASE
    assert "perri" in CHATBOT_KNOWLEDGE_BASE


def test_chatbot_markowitz_answer_mentions_frontier_and_sharpe():
    service = ChatbotService()

    result = service.answer_question(
        question="Explicame Markowitz y la frontera eficiente",
        mode="general",
        module="markowitz",
    )

    assert result["supported"] is True
    assert "frontera eficiente" in result["answer"]
    assert "Sharpe" in result["answer"]


def test_chatbot_markowitz_statistical_answer_mentions_covariance():
    service = ChatbotService()

    result = service.answer_question(
        question="Como funciona Markowitz estadisticamente?",
        mode="estadistico",
        module="markowitz",
    )

    assert result["supported"] is True
    assert "covarianzas" in result["answer"]
    assert "correlaciones" in result["answer"]


def test_chatbot_perri_answer_mentions_exact_sizes_horizons_and_objectives():
    service = ChatbotService()

    result = service.answer_question(
        question="Que es Perri institucional?",
        mode="general",
        module="perri",
    )

    assert result["supported"] is True
    assert "5, 10 y 15 activos" in result["answer"]
    assert "1, 3 y 5 anos" in result["answer"]
    assert "min_risk" in result["answer"]
    assert "max_sharpe" in result["answer"]
    assert "max_return" in result["answer"]


def test_chatbot_detects_markowitz_and_perri_together():
    service = ChatbotService()

    result = service.answer_question(
        question="Como se compara Markowitz contra Perri?",
        mode="general",
    )

    assert result["supported"] is True
    assert "markowitz" in result["topics"]
    assert "perri" in result["topics"]
