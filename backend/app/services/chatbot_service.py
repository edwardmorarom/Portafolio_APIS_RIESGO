from __future__ import annotations

import re

from app.clients.llm_client import LLMClient
from app.core.chatbot_knowledge import CHATBOT_KNOWLEDGE_BASE
from app.core.chatbot_scope import (
    FINANCIAL_SCOPE_FOLLOWUPS,
    FINANCIAL_SCOPE_MESSAGE,
    is_financial_question,
)


class ChatbotService:
    """
    Servicio base del chatbot experto en teoría del riesgo.

    Esta versión:
    - Mantiene motor experto local como fallback seguro.
    - Usa una base de conocimiento local separada en core/chatbot_knowledge.py.
    - Recibe LLMClient por inyección de dependencias.
    - Solo usa IA real si LLMClient está habilitado y retorna respuesta.
    - Evita llamadas externas cuando llm_provider=local.
    """

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client
        self.knowledge_base = CHATBOT_KNOWLEDGE_BASE

    def _normalize(self, text: str) -> str:
        value = text.strip().lower()
        value = re.sub(r"\s+", " ", value)
        return value

    def _detect_topics(self, question: str, module: str | None = None) -> list[str]:
        normalized = self._normalize(question)

        detected = []

        if module and module in self.knowledge_base:
            detected.append(module)

        for topic, payload in self.knowledge_base.items():
            keywords = payload["keywords"]
            if any(keyword in normalized for keyword in keywords):
                if topic not in detected:
                    detected.append(topic)

        return detected

    def _build_llm_context(self, topic: str, payload: dict, local_answer: str) -> str:
        return (
            f"Tema detectado: {topic}\n"
            f"Fuente interna: {payload['title']}\n"
            f"Tipo de fuente: {payload['source_type']}\n"
            f"Referencia: {payload['reference']}\n"
            f"Respuesta base local: {local_answer}"
        )

    def answer_question(
        self,
        question: str,
        mode: str = "general",
        module: str | None = None,
    ) -> dict:
        normalized_question = question.strip()
        normalized_mode = mode.strip().lower()
        normalized_module = module.strip().lower() if module else None

        if not is_financial_question(
            question=normalized_question,
            module=normalized_module,
        ):
            return {
                "question": normalized_question,
                "mode": normalized_mode,
                "module": normalized_module,
                "supported": False,
                "answer": FINANCIAL_SCOPE_MESSAGE,
                "topics": [],
                "sources": [],
                "suggested_followups": FINANCIAL_SCOPE_FOLLOWUPS,
            }

        if not is_financial_question(
            question=normalized_question,
            module=normalized_module,
        ):
            return {
                "question": normalized_question,
                "mode": normalized_mode,
                "module": normalized_module,
                "supported": False,
                "answer": FINANCIAL_SCOPE_MESSAGE,
                "topics": [],
                "sources": [],
                "suggested_followups": FINANCIAL_SCOPE_FOLLOWUPS,
            }

        topics = self._detect_topics(
            question=normalized_question,
            module=normalized_module,
        )

        if not topics:
            return {
                "question": normalized_question,
                "mode": normalized_mode,
                "module": normalized_module,
                "supported": False,
                "answer": (
                    "No encontré soporte suficiente en la base de conocimiento local del proyecto para responder "
                    "esa pregunta con seguridad. Reformula la pregunta usando un módulo como VaR, CVaR, CAPM, "
                    "Markowitz, GARCH, Perri, Nelson-Siegel o Black-Scholes."
                ),
                "topics": [],
                "sources": [],
                "suggested_followups": [
                    "¿Qué es el VaR?",
                    "¿Cómo se interpreta CAPM?",
                    "¿Qué hace Perri en el proyecto?",
                ],
            }

        selected_topic = topics[0]
        payload = self.knowledge_base[selected_topic]

        local_answer = payload["estadistico"] if normalized_mode == "estadistico" else payload["general"]
        answer = local_answer

        if self.llm_client is not None:
            context = self._build_llm_context(
                topic=selected_topic,
                payload=payload,
                local_answer=local_answer,
            )
            llm_answer = self.llm_client.generate_answer(
                question=normalized_question,
                context=context,
                mode=normalized_mode,
            )

            if llm_answer:
                answer = llm_answer

        sources = [
            {
                "title": payload["title"],
                "source_type": payload["source_type"],
                "reference": payload["reference"],
            }
        ]

        return {
            "question": normalized_question,
            "mode": normalized_mode,
            "module": normalized_module,
            "supported": True,
            "answer": answer,
            "topics": topics,
            "sources": sources,
            "suggested_followups": payload["followups"],
        }
