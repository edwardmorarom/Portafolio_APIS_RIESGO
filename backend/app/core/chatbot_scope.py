from __future__ import annotations

from app.core.chatbot_financial_topics import (
    get_financial_keywords,
    get_financial_modules,
    get_financial_topic_keys,
)

FINANCIAL_MODULES = get_financial_modules()
FINANCIAL_KEYWORDS = get_financial_keywords()
FINANCIAL_TOPICS = set(get_financial_topic_keys())

FINANCIAL_SCOPE_MESSAGE = (
    "Esta pregunta está fuera del alcance financiero del chatbot experto. "
    "Puedo ayudarte con teoría del riesgo, VaR, CVaR, CAPM, Markowitz, GARCH, Perri, "
    "Nelson-Siegel, Black-Scholes, benchmark, macroeconomía financiera, KYC, RoboAdvisor "
    "y métricas del proyecto."
)

FINANCIAL_SCOPE_FOLLOWUPS = [
    "¿Qué es el VaR y cómo se interpreta?",
    "¿Cómo se compara Markowitz contra Perri?",
    "¿Qué significa beta en CAPM?",
]


def is_financial_question(question: str, module: str | None = None) -> bool:
    normalized_question = question.strip().lower()
    normalized_module = module.strip().lower() if module else None

    if normalized_module in FINANCIAL_MODULES:
        return True

    return any(keyword in normalized_question for keyword in FINANCIAL_KEYWORDS)
