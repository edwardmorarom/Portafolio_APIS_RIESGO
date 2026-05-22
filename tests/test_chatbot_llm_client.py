from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.chatbot_service import ChatbotService  # noqa: E402
from app.clients.llm_client import LLMClient  # noqa: E402
from app.core.settings import Settings  # noqa: E402


class FakeLLMClient:
    def generate_answer(self, question: str, context: str, mode: str) -> str:
        assert "Tema detectado" in context
        assert question
        assert mode in {"general", "estadistico"}
        return "Respuesta generada por cliente IA simulado sobre VaR."


def test_chatbot_service_uses_llm_answer_when_available():
    service = ChatbotService(llm_client=FakeLLMClient())

    result = service.answer_question(
        question="Explícame el VaR",
        mode="general",
        module="var",
    )

    assert result["supported"] is True
    assert result["answer"] == "Respuesta generada por cliente IA simulado sobre VaR."
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


def test_llm_client_enables_groq_with_groq_api_key():
    settings = Settings(
        llm_provider="groq",
        llm_model="local-expert",
        llm_api_key=None,
        groq_api_key="test-groq-key",
    )

    client = LLMClient(settings)

    assert client.is_enabled() is True
    assert client.model == "llama-3.1-8b-instant"
    assert client.base_url == "https://api.groq.com/openai/v1"


def test_llm_client_parses_groq_chat_completion(monkeypatch):
    calls = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": "Respuesta Groq simulada."
                        }
                    }
                ]
            }

    def fake_post(url, headers, json, timeout):
        calls["url"] = url
        calls["headers"] = headers
        calls["json"] = json
        calls["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.clients.llm_client.requests.post", fake_post)

    settings = Settings(
        llm_provider="groq",
        llm_model="llama-3.1-8b-instant",
        groq_api_key="test-groq-key",
    )
    client = LLMClient(settings)

    answer = client.generate_answer(
        question="Que es VaR?",
        context="Contexto interno de riesgo.",
        mode="general",
    )

    assert answer == "Respuesta Groq simulada."
    assert calls["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert calls["headers"]["Authorization"] == "Bearer test-groq-key"
    assert calls["json"]["model"] == "llama-3.1-8b-instant"
    assert calls["json"]["messages"]
