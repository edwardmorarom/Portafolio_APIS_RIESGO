from __future__ import annotations

FINANCIAL_MODULES = {
    "var",
    "cvar",
    "capm",
    "markowitz",
    "garch",
    "perri",
    "black_scholes",
    "nelson_siegel",
    "risk",
    "portfolio",
    "valuation",
    "benchmark",
    "macro",
    "investor",
    "roboadvisor",
}

FINANCIAL_KEYWORDS = {
    "activo",
    "activos",
    "acciones",
    "alpha",
    "alfa",
    "benchmark",
    "beta",
    "black-scholes",
    "bonos",
    "capm",
    "cartera",
    "cvar",
    "drawdown",
    "eficiente",
    "egarch",
    "expected shortfall",
    "financiero",
    "frontera eficiente",
    "garch",
    "inversion",
    "inversión",
    "inversionista",
    "kyc",
    "macro",
    "markowitz",
    "mercado",
    "monte carlo",
    "nelson",
    "opciones",
    "perri",
    "portafolio",
    "rentabilidad",
    "retorno",
    "riesgo",
    "roboadvisor",
    "sharpe",
    "tasa libre de riesgo",
    "tasas",
    "teoria del riesgo",
    "teoría del riesgo",
    "umbral",
    "umbrales",
    "var",
    "value at risk",
    "valor en riesgo",
    "volatilidad",
}

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
