from __future__ import annotations

import re

from app.clients.llm_client import LLMClient
from app.core.chatbot_course_notes import find_course_notes
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

        scored: list[tuple[int, str]] = []

        for topic, payload in self.knowledge_base.items():
            keywords = payload["keywords"]
            score = sum(3 if keyword == topic and keyword in normalized else 1 for keyword in keywords if keyword in normalized)
            if score > 0:
                scored.append((score, topic))

        if not scored and module and module in self.knowledge_base:
            scored.append((1, module))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [topic for _, topic in scored]

    def _build_llm_context(self, topic: str, payload: dict, local_answer: str, question: str) -> str:
        course_notes = " ".join(find_course_notes(question))
        return (
            f"Tema detectado: {topic}\n"
            f"Fuente interna: {payload['title']}\n"
            f"Tipo de fuente: {payload['source_type']}\n"
            f"Referencia: {payload['reference']}\n"
            f"Notas de clase disponibles: {course_notes or 'Sin nota adicional'}\n"
            f"Respuesta base local: {local_answer}"
        )

    def _llm_answer_matches_topic(self, answer: str, topic: str, payload: dict) -> bool:
        normalized = self._normalize(answer)
        if topic == "kyc":
            return True

        kyc_terms = ["kyc", "perfil del inversionista", "perfil de riesgo", "tolerancia al riesgo"]
        topic_terms = [topic, str(payload.get("title", "")).lower()]
        topic_terms.extend(str(keyword).lower() for keyword in payload.get("keywords", [])[:6])

        mentions_kyc = any(term in normalized for term in kyc_terms)
        mentions_topic = any(term and term in normalized for term in topic_terms)
        if mentions_kyc and not mentions_topic:
            return False
        return True

    def _portfolio_context_text(self, portfolio_context: dict | None) -> str:
        if not isinstance(portfolio_context, dict) or not portfolio_context:
            return ""

        tickers = portfolio_context.get("tickers") or []
        weights = portfolio_context.get("weights_pct") or []
        horizon = portfolio_context.get("horizon") or portfolio_context.get("horizon_type")
        benchmark = portfolio_context.get("benchmark") or {}
        benchmark_ticker = benchmark.get("ticker") if isinstance(benchmark, dict) else benchmark

        parts = []
        if tickers:
            if weights and len(weights) == len(tickers):
                pairs = [f"{ticker} {float(weights[index]):.2f}%" for index, ticker in enumerate(tickers)]
                parts.append("Portafolio activo: " + ", ".join(pairs))
            else:
                parts.append("Portafolio activo: " + ", ".join([str(ticker) for ticker in tickers]))
        if horizon:
            parts.append(f"Horizonte: {horizon}")
        if benchmark_ticker:
            parts.append(f"Benchmark: {benchmark_ticker}")

        return ". ".join(parts)

    def _adapt_local_answer(self, question: str, base_answer: str, portfolio_context: dict | None) -> str:
        normalized = self._normalize(question)
        answer = base_answer

        if any(word in normalized for word in ["sustentar", "explicar", "profesor", "exposicion", "exposición"]):
            answer += " Para sustentación, explica primero el objetivo del módulo, luego el indicador calculado y finalmente la decisión financiera que permite tomar."

        if any(word in normalized for word in ["kpi", "resultado", "favorable", "desfavorable", "interpreto", "interpretar"]):
            answer += " Si el KPI muestra mayor retorno con menor riesgo relativo, la lectura es favorable; si aumenta la pérdida esperada o la volatilidad, la lectura exige cautela."

        portfolio_text = self._portfolio_context_text(portfolio_context)
        if portfolio_text and any(word in normalized for word in ["portafolio", "activo", "acciones", "pesos", "benchmark", "horizonte"]):
            answer += f" Con el contexto actual: {portfolio_text}. No invento resultados numéricos que no hayan sido calculados en pantalla."

        course_notes = find_course_notes(question, limit=1)
        if course_notes and not any(note in answer for note in course_notes):
            answer += f" Nota de clase: {course_notes[0]}"

        return answer

    def answer_question(
        self,
        question: str,
        mode: str = "general",
        module: str | None = None,
        portfolio_context: dict | None = None,
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

        topics = self._detect_topics(
            question=normalized_question,
            module=normalized_module,
        )

        if not topics:
            broad_answer = self._adapt_local_answer(
                question=normalized_question,
                base_answer=(
                    "Puedo responder con el contexto del proyecto aunque la pregunta no coincida con una plantilla exacta. "
                    "El dashboard analiza un portafolio desde rendimiento, riesgo, benchmark, modelos estadísticos, "
                    "stress testing y Machine Learning. Si preguntas por un resultado numérico específico, necesito que "
                    "ese resultado esté calculado o visible en el módulo correspondiente."
                ),
                portfolio_context=portfolio_context,
            )
            if self.llm_client is not None:
                llm_answer = self.llm_client.generate_answer(
                    question=normalized_question,
                    context=(
                        "Contexto general: dashboard Streamlit de riesgo financiero con módulos de portafolio, "
                        "rendimientos, técnico, GARCH, CAPM, VaR/CVaR/Kupiec, Markowitz, macro/benchmark, renta fija, "
                        "opciones, stress testing, ML y reportes. Notas de clase: "
                        + " ".join(find_course_notes(normalized_question))
                        + " "
                        + self._portfolio_context_text(portfolio_context)
                    ),
                    mode=normalized_mode,
                )
                if llm_answer:
                    broad_answer = llm_answer

            return {
                "question": normalized_question,
                "mode": normalized_mode,
                "module": normalized_module,
                "supported": True,
                "answer": broad_answer,
                "topics": [],
                "sources": [],
                "suggested_followups": [
                    "¿Qué hace este dashboard?",
                    "¿Cómo afecta el horizonte al riesgo?",
                    "¿Cómo explico el módulo de ML?",
                ],
            }

        selected_topic = topics[0]
        payload = self.knowledge_base[selected_topic]

        local_answer = payload["estadistico"] if normalized_mode == "estadistico" else payload["general"]
        answer = self._adapt_local_answer(
            question=normalized_question,
            base_answer=local_answer,
            portfolio_context=portfolio_context,
        )

        if self.llm_client is not None:
            context = self._build_llm_context(
                topic=selected_topic,
                payload=payload,
                local_answer=answer,
                question=normalized_question,
            )
            llm_answer = self.llm_client.generate_answer(
                question=normalized_question,
                context=context,
                mode=normalized_mode,
            )

            if llm_answer and self._llm_answer_matches_topic(llm_answer, selected_topic, payload):
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
