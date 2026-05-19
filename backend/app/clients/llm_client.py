from __future__ import annotations

from app.core.settings import Settings


class LLMClient:
    """
    Cliente interno para integrar un proveedor de IA real en el chatbot.

    Estado actual:
    - No hace llamadas externas.
    - Lee configuración desde Settings.
    - Permite detectar si el modo IA está habilitado.
    - Mantiene el modo local como fallback seguro.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = settings.llm_provider.strip().lower()
        self.model = settings.llm_model.strip()
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url

    def is_enabled(self) -> bool:
        return self.provider != "local" and bool(self.api_key)

    def generate_answer(
        self,
        question: str,
        context: str,
        mode: str,
    ) -> str | None:
        """
        Punto de extensión para IA real.

        Retorna None mientras no exista un proveedor externo implementado.
        El ChatbotService debe usar su respuesta local cuando este método retorne None.
        """
        if not self.is_enabled():
            return None

        return None
