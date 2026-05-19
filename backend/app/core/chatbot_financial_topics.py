from __future__ import annotations

CHATBOT_FINANCIAL_TOPIC_CATALOG = {
    "var": {
        "label": "VaR",
        "description": "Valor en riesgo, pérdida máxima esperada bajo un nivel de confianza.",
        "keywords": ["var", "value at risk", "valor en riesgo", "riesgo extremo"],
    },
    "cvar": {
        "label": "CVaR",
        "description": "Pérdida esperada condicional cuando se supera el VaR.",
        "keywords": ["cvar", "expected shortfall", "cola", "pérdida esperada"],
    },
    "capm": {
        "label": "CAPM",
        "description": "Modelo de valoración de activos basado en beta, alpha y retorno esperado.",
        "keywords": ["capm", "beta", "alpha", "alfa", "retorno esperado", "mercado"],
    },
    "markowitz": {
        "label": "Markowitz",
        "description": "Optimización de portafolios, frontera eficiente, mínima varianza y máximo Sharpe.",
        "keywords": ["markowitz", "frontera eficiente", "sharpe", "mínima varianza", "minima varianza", "portafolio"],
    },
    "garch": {
        "label": "GARCH",
        "description": "Modelación de volatilidad condicional con ARCH, GARCH y EGARCH.",
        "keywords": ["garch", "arch", "egarch", "volatilidad condicional", "heterocedasticidad"],
    },
    "perri": {
        "label": "Perri institucional",
        "description": "Optimización institucional con portafolios exactos por tamaño, horizonte y objetivo.",
        "keywords": ["perri", "umbrales", "institucional", "5 activos", "10 activos", "15 activos"],
    },
    "black_scholes": {
        "label": "Black-Scholes",
        "description": "Valoración de opciones financieras y cálculo de griegas.",
        "keywords": ["black-scholes", "black scholes", "opción", "opciones", "call", "put", "griegas"],
    },
    "nelson_siegel": {
        "label": "Nelson-Siegel",
        "description": "Modelación de curva de tasas mediante nivel, pendiente y curvatura.",
        "keywords": ["nelson", "siegel", "curva de tasas", "yield curve", "tasas"],
    },
    "benchmark": {
        "label": "Benchmark",
        "description": "Comparación de portafolio contra referencia de mercado.",
        "keywords": ["benchmark", "tracking error", "information ratio", "alpha de jensen", "drawdown"],
    },
    "macro_financiero": {
        "label": "Macro financiero",
        "description": "Tasa libre de riesgo, inflación, FX y variables macro aplicadas al análisis financiero.",
        "keywords": ["macro", "macroeconomía financiera", "tasa libre de riesgo", "inflación", "fx", "tipo de cambio"],
    },
    "kyc": {
        "label": "KYC / perfil inversionista",
        "description": "Preferencias, perfil de riesgo y horizonte del inversionista.",
        "keywords": ["kyc", "perfil de riesgo", "inversionista", "horizonte", "preferencias"],
    },
    "roboadvisor": {
        "label": "RoboAdvisor",
        "description": "Sugerencia automatizada de portafolios según perfil y activos.",
        "keywords": ["roboadvisor", "asesor automático", "portafolio sugerido", "perfil conservador", "perfil agresivo"],
    },
}

CHATBOT_ALLOWED_FINANCIAL_MODULES = set(CHATBOT_FINANCIAL_TOPIC_CATALOG.keys()) | {
    "risk",
    "portfolio",
    "valuation",
    "macro",
    "investor",
}

CHATBOT_ALLOWED_FINANCIAL_KEYWORDS = {
    keyword
    for topic in CHATBOT_FINANCIAL_TOPIC_CATALOG.values()
    for keyword in topic["keywords"]
} | {
    "activo",
    "activos",
    "acciones",
    "bonos",
    "cartera",
    "correlacion",
    "correlación",
    "diversificación",
    "financiero",
    "inversion",
    "inversión",
    "mercado",
    "monte carlo",
    "rentabilidad",
    "retorno",
    "riesgo",
    "teoria del riesgo",
    "teoría del riesgo",
    "volatilidad",
}


def get_financial_topic_keys() -> list[str]:
    return sorted(CHATBOT_FINANCIAL_TOPIC_CATALOG.keys())


def get_financial_keywords() -> set[str]:
    return set(CHATBOT_ALLOWED_FINANCIAL_KEYWORDS)


def get_financial_modules() -> set[str]:
    return set(CHATBOT_ALLOWED_FINANCIAL_MODULES)
