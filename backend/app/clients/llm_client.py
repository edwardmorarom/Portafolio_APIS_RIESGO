from __future__ import annotations

import requests

from app.core.settings import Settings


class LLMClient:
    """
    Cliente interno para integrar IA real en el chatbot.

    Proveedor soportado:
    - local: no llama IA externa.
    - gemini: usa Gemini API via REST.

    Si la IA falla, retorna None para conservar fallback local.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = settings.llm_provider.strip().lower()
        self.model = settings.llm_model.strip()
        self.api_key = settings.llm_api_key
        self.base_url = (
            settings.llm_base_url
            or "https://generativelanguage.googleapis.com/v1beta"
        )

    def is_enabled(self) -> bool:
        return self.provider == "gemini" and bool(self.api_key)

    def _build_prompt(self, question: str, context: str, mode: str) -> str:
        return (
            "Eres un chatbot experto del Proyecto Integrador de Riesgo USTA.\n"
            "Responde en espanol claro, tecnico y breve.\n"
            "Usa el contexto interno como fuente principal.\n"
            "No inventes datos fuera del contexto.\n"
            "Solo menciona KYC si la pregunta trata explícitamente sobre perfil del inversionista o riesgo personal.\n\n"
            f"Modo de respuesta: {mode}\n\n"
            f"Contexto interno:\n{context}\n\n"
            f"Pregunta del usuario:\n{question}\n\n"
            "Respuesta:"
        )

    def generate_answer(
        self,
        question: str,
        context: str,
        mode: str,
    ) -> str | None:
        if not self.is_enabled():
            return None

        url = f"{self.base_url}/models/{self.model}:generateContent"

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": self._build_prompt(
                                question=question,
                                context=context,
                                mode=mode,
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 500,
            },
        }

        try:
            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": str(self.api_key),
                },
                json=payload,
                timeout=self.settings.external_api_timeout_seconds,
            )
            response.raise_for_status()

            data = response.json()
            candidates = data.get("candidates", [])

            if not candidates:
                return None

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])

            if not parts:
                return None

            text = parts[0].get("text")

            if not text:
                return None

            return str(text).strip()

        except Exception:
            return None
