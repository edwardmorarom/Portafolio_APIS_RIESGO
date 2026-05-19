from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.chatbot_service import ChatbotService  # noqa: E402


class FakeLLMClient:
    def generate_answer(self, question: str, context: str, mode: str) -> str:
        assert "Tema detectado" in context
        assert question
        assert mode in {"general", "estadistico"}
        return "Respuesta generada por cliente IA simulado."


def test_chatbot_service_uses_llm_answer_when_available():
    service = ChatbotService(llm_client=FakeLLMClient())

    result = service.answer_question(
        question="Explícame el VaR",
        mode="general",
        module="var",
    )

    assert result["supported"] is True
    assert result["answer"] == "Respuesta generada por cliente IA simulado."
    assert result["sources"]


def test_chatbot_service_keeps_local_answer_without_llm_client():
    service = ChatbotService(llm_client=None)

    result = service.answer_question(
        question="Explícame el VaR",
        mode="general",
        module="var",
    )

    assert result["supported"] is True
    assert "El VaR estima" in result["answer"]
