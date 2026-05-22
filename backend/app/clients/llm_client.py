from __future__ import annotations

import requests

from app.core.settings import Settings


class LLMClient:
    """
    Cliente interno para integrar IA real en el chatbot.

    Proveedor soportado:
    - local: no llama IA externa.
    - gemini: usa Gemini API via REST.
    - groq: usa GroqCloud con API compatible OpenAI.

    Si la IA falla, retorna None para conservar fallback local.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = settings.llm_provider.strip().lower()
        self.model = self._resolve_model(settings.llm_model.strip())
        self.api_key = self._resolve_api_key()
        self.base_url = self._resolve_base_url()

    def is_enabled(self) -> bool:
        return self.provider in {"gemini", "groq"} and bool(self.api_key)

    def _resolve_model(self, configured_model: str) -> str:
        if self.provider == "groq" and configured_model in {"", "local-expert"}:
            return "llama-3.1-8b-instant"
        return configured_model

    def _resolve_api_key(self) -> str | None:
        if self.provider == "groq":
            return self.settings.groq_api_key
        return self.settings.llm_api_key

    def _resolve_base_url(self) -> str:
        configured_base_url = (
            self.settings.llm_base_url.rstrip("/")
            if self.settings.llm_base_url
            else None
        )
        if self.provider == "groq":
            if configured_base_url and "generativelanguage.googleapis.com" not in configured_base_url:
                return configured_base_url
            return "https://api.groq.com/openai/v1"
        if self.provider == "gemini" and configured_base_url and "api.groq.com" not in configured_base_url:
            return configured_base_url
        return "https://generativelanguage.googleapis.com/v1beta"

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

        if self.provider == "groq":
            return self._generate_groq_answer(
                question=question,
                context=context,
                mode=mode,
            )

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

    def _generate_groq_answer(
        self,
        question: str,
        context: str,
        mode: str,
    ) -> str | None:
        url = f"{self.base_url}/chat/completions"
        prompt = self._build_prompt(
            question=question,
            context=context,
            mode=mode,
        )
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente financiero academico del Proyecto Integrador de Riesgo USTA. "
                        "Responde con claridad, sin inventar resultados numericos y sin cambiar el tema a KYC "
                        "salvo que el usuario pregunte por perfil del inversionista."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 500,
        }

        try:
            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json=payload,
                timeout=self.settings.external_api_timeout_seconds,
            )
            response.raise_for_status()

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                return None

            message = choices[0].get("message", {})
            content = message.get("content")
            if not content:
                return None

            return str(content).strip()

        except Exception:
            return None
