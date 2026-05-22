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

        forced_topic = self._forced_topic_from_question(normalized)
        if forced_topic:
            return [forced_topic]

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

    def _is_greeting_question(self, normalized: str) -> bool:
        greeting_patterns = [
            r"^hola[!. ]*$",
            r"^hola[, ]+como estas[?!. ]*$",
            r"^hola[, ]+como estás[?!. ]*$",
            r"^hola[, ]+como estas\?[ ]*$",
            r"^hola[, ]+como estás\?[ ]*$",
            r"^buenos dias[!. ]*$",
            r"^buenas tardes[!. ]*$",
            r"^buenas noches[!. ]*$",
            r"^buenas[!. ]*$",
        ]
        return any(re.search(pattern, normalized) for pattern in greeting_patterns)

    def _forced_topic_from_question(self, normalized: str) -> str | None:
        if (
            re.search(r"\bvar\b", normalized)
            and any(word in normalized for word in ["mejor", "modelo", "metodo", "método", "elegir", "escojo", "escoger"])
        ):
            return "kupiec"
        if re.search(r"\bvar\b", normalized) or "valor en riesgo" in normalized or "value at risk" in normalized:
            return "var"
        if "cvar" in normalized or "expected shortfall" in normalized:
            return "cvar"
        if any(
            term in normalized
            for term in [
                "renta fija",
                "bono",
                "bonos",
                "vencimiento",
                "fecha de vencimiento",
                "cupon",
                "cupón",
                "precio limpio",
                "precio sucio",
                "yield",
                "duracion",
                "duración",
                "dv01",
            ]
        ) or re.search(r"\btes\b", normalized):
            return "nelson_siegel"
        if any(
            term in normalized
            for term in [
                "gauss",
                "gaussiana",
                "gausiana",
                "normal",
                "student",
                "t student",
                "t-student",
                "ged",
                "distribucion",
                "distribución",
            ]
        ) and any(
            term in normalized
            for term in [
                "serie",
                "series",
                "tiempo",
                "financiera",
                "financieras",
                "rendimiento",
                "rendimientos",
                "cola",
                "colas",
            ]
        ):
            return "garch"
        if "horizonte" in normalized or "plazo" in normalized:
            return "horizonte"
        if "que hace este dashboard" in normalized or "qué hace este dashboard" in normalized:
            return "dashboard"
        if "machine learning" in normalized or re.search(r"\bml\b", normalized):
            return "ml"
        return None

    def _build_llm_context(self, topic: str, payload: dict, question: str, portfolio_context: dict | None = None) -> str:
        course_notes = " ".join(find_course_notes(question))
        return (
            f"Tema detectado: {topic}\n"
            f"Fuente interna: {payload['title']}\n"
            f"Tipo de fuente: {payload['source_type']}\n"
            f"Referencia: {payload['reference']}\n"
            f"Notas de clase disponibles: {course_notes or 'Sin nota adicional'}\n"
            f"Contexto del portafolio: {self._portfolio_context_text(portfolio_context) or 'No disponible'}\n"
            "Instruccion: responde la pregunta real del usuario con razonamiento breve. "
            "No copies una respuesta fija ni cambies el tema a KYC salvo que la pregunta trate de perfil del inversionista."
        )

    def _llm_answer_matches_topic(self, answer: str, topic: str, payload: dict, question: str = "") -> bool:
        normalized = self._normalize(answer)
        normalized_question = self._normalize(question)
        if topic == "kyc":
            return True

        kyc_terms = ["kyc", "perfil del inversionista", "perfil de riesgo", "tolerancia al riesgo"]
        mentions_kyc = any(term in normalized for term in kyc_terms)
        if mentions_kyc:
            return False

        required_terms_by_topic = {
            "garch": [
                "garch",
                "arch",
                "egarch",
                "volatilidad",
                "distribucion",
                "distribución",
                "normal",
                "gauss",
                "student",
                "ged",
                "cola",
            ],
            "ml": [
                "machine learning",
                "ml",
                "modelo",
                "ridge",
                "lasso",
                "gradient",
                "boosting",
                "retorno",
                "prediccion",
                "predicción",
            ],
            "horizonte": ["horizonte", "plazo", "tiempo", "ventana", "largo plazo", "corto plazo"],
            "nelson_siegel": ["renta fija", "bono", "cupón", "cupon", "vencimiento", "yield", "dv01", "duracion", "duración"],
            "var": ["var", "value at risk", "valor en riesgo", "cuantil", "perdida", "pérdida"],
            "kupiec": ["kupiec", "excedencia", "violacion", "violación", "backtesting", "p-value"],
        }
        required_terms = required_terms_by_topic.get(topic)
        if required_terms and not any(term in normalized for term in required_terms):
            return False

        if topic == "ml" and any(
            term in normalized_question
            for term in ["3 modelos", "tres modelos", "mas adecuado", "más adecuado", "mejor modelo"]
        ):
            model_terms = ["ridge", "lasso", "gradient", "boosting"]
            if not any(term in normalized for term in model_terms):
                return False

        if topic == "garch" and any(
            term in normalized_question
            for term in ["gauss", "normal", "student", "distribucion", "distribución", "series de tiempo"]
        ):
            distribution_terms = ["normal", "gauss", "student", "ged", "cola", "distribucion", "distribución"]
            if not any(term in normalized for term in distribution_terms):
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

    def _llm_configured(self) -> bool:
        if self.llm_client is None:
            return False
        is_enabled = getattr(self.llm_client, "is_enabled", None)
        if callable(is_enabled):
            return bool(is_enabled())
        return False

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
        normalized_for_intent = self._normalize(normalized_question)

        if self._is_greeting_question(normalized_for_intent):
            greeting_context = (
                "Contexto general: eres el asistente IA del dashboard de riesgo financiero. "
                "Saluda de forma breve y ofrece ayuda sobre portafolio, VaR, CVaR, CAPM, GARCH, "
                "Markowitz, renta fija, opciones, stress testing, Machine Learning y reporte."
            )
            llm_answer = None
            if self.llm_client is not None:
                llm_answer = self.llm_client.generate_answer(
                    question=normalized_question,
                    context=greeting_context,
                    mode=normalized_mode,
                )
                if llm_answer and "kyc" in self._normalize(llm_answer):
                    llm_answer = None

            answer = llm_answer or (
                "Hola, estoy bien y listo para ayudarte. Puedo explicarte el dashboard, interpretar KPIs "
                "o aterrizar conceptos como VaR, CAPM, GARCH, renta fija, opciones, stress testing y ML."
            )

            return {
                "question": normalized_question,
                "mode": normalized_mode,
                "module": normalized_module,
                "supported": True,
                "answer": answer,
                "topics": [],
                "sources": [],
                "suggested_followups": [
                    "¿Para qué sirve el módulo de renta fija?",
                    "¿Cómo elijo el mejor método de VaR?",
                    "¿Qué hace este dashboard?",
                ],
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
                else:
                    broad_answer = self._adapt_local_answer(
                        question=normalized_question,
                        base_answer=(
                            "Puedo responder con el contexto del proyecto aunque la IA externa no esté disponible. "
                            "El dashboard analiza un portafolio desde rendimiento, riesgo, benchmark, modelos estadísticos, "
                            "stress testing y Machine Learning. Si preguntas por un resultado numérico específico, necesito que "
                            "ese resultado esté calculado o visible en el módulo correspondiente."
                        ),
                        portfolio_context=portfolio_context,
                    )
            else:
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
                question=normalized_question,
                portfolio_context=portfolio_context,
            )
            llm_answer = self.llm_client.generate_answer(
                question=normalized_question,
                context=context,
                mode=normalized_mode,
            )

            if llm_answer and self._llm_answer_matches_topic(
                answer=llm_answer,
                topic=selected_topic,
                payload=payload,
                question=normalized_question,
            ):
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
