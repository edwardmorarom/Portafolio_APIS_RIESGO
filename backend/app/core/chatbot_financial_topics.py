from __future__ import annotations

CHATBOT_FINANCIAL_TOPIC_CATALOG = {
    "var": {
        "label": "VaR",
        "description": "Valor en riesgo, perdida maxima esperada bajo un nivel de confianza.",
        "keywords": ["var", "value at risk", "valor en riesgo", "riesgo extremo", "percentil", "cuantil"],
    },
    "cvar": {
        "label": "CVaR",
        "description": "Perdida esperada condicional cuando se supera el VaR.",
        "keywords": ["cvar", "expected shortfall", "cola", "perdida esperada", "pérdida esperada", "riesgo de cola"],
    },
    "kupiec": {
        "label": "Backtesting de Kupiec",
        "description": "Prueba de proporcion de fallas para validar excedencias del VaR.",
        "keywords": [
            "kupiec",
            "backtesting",
            "excedencias",
            "violaciones",
            "lr_pof",
            "proportion of failures",
            "mejor metodo var",
            "mejor método var",
            "elegir var",
            "modelo var",
        ],
    },
    "capm": {
        "label": "CAPM",
        "description": "Modelo de valoracion de activos basado en beta, alpha y retorno esperado.",
        "keywords": ["capm", "beta", "alpha", "alfa", "retorno esperado", "mercado"],
    },
    "markowitz": {
        "label": "Markowitz",
        "description": "Optimizacion de portafolios, frontera eficiente, minima varianza y maximo Sharpe.",
        "keywords": ["markowitz", "frontera eficiente", "sharpe", "minima varianza", "mínima varianza", "portafolio"],
    },
    "garch": {
        "label": "GARCH",
        "description": "Modelacion de volatilidad condicional con ARCH, GARCH y EGARCH.",
        "keywords": [
            "garch",
            "arch",
            "egarch",
            "egarhc",
            "volatilidad condicional",
            "heterocedasticidad",
            "distribucion",
            "distribución",
            "gaussiana",
            "normal",
            "student",
            "gaussiaana",
            "t student",
            "series de tiempo",
        ],
    },
    "perri": {
        "label": "Perri institucional",
        "description": "Optimizacion institucional con portafolios exactos por tamano, horizonte y objetivo.",
        "keywords": ["perri", "umbrales", "institucional", "5 activos", "10 activos", "15 activos"],
    },
    "black_scholes": {
        "label": "Black-Scholes",
        "description": "Valoracion de opciones financieras y calculo de griegas.",
        "keywords": ["black-scholes", "black scholes", "opcion", "opción", "opciones", "call", "put", "griegas"],
    },
    "nelson_siegel": {
        "label": "Nelson-Siegel",
        "description": "Modelacion de curva de tasas, bonos TES, vencimiento, duracion y DV01.",
        "keywords": [
            "renta fija",
            "bono",
            "bonos",
            "tes",
            "nelson",
            "siegel",
            "curva de tasas",
            "yield curve",
            "tasas",
            "yield",
            "cupon",
            "cupón",
            "vencimiento",
            "fecha de vencimiento",
            "precio limpio",
            "precio sucio",
            "duracion",
            "duración",
            "dv01",
        ],
    },
    "benchmark": {
        "label": "Benchmark",
        "description": "Comparacion de portafolio contra referencia de mercado.",
        "keywords": ["benchmark", "spy", "s&p 500", "sp500", "acwi", "msci acwi", "tracking error", "information ratio", "alpha de jensen", "drawdown"],
    },
    "macro_financiero": {
        "label": "Macro financiero",
        "description": "Tasa libre de riesgo, inflacion, FX y variables macro aplicadas al analisis financiero.",
        "keywords": ["macro", "macroeconomia financiera", "macroeconomía financiera", "tasa libre de riesgo", "inflacion", "inflación", "fx", "tipo de cambio"],
    },
    "kyc": {
        "label": "KYC / perfil inversionista",
        "description": "Preferencias, perfil de riesgo y horizonte del inversionista.",
        "keywords": ["kyc", "perfil de riesgo", "inversionista", "horizonte", "preferencias"],
    },
    "roboadvisor": {
        "label": "RoboAdvisor",
        "description": "Sugerencia automatizada de portafolios segun perfil y activos.",
        "keywords": ["roboadvisor", "asesor automatico", "asesor automático", "portafolio sugerido", "perfil conservador", "perfil agresivo"],
    },
    "ml": {
        "label": "Machine Learning",
        "description": "Prediccion de retorno esperado con variables de riesgo y endpoint /ml/predict.",
        "keywords": ["machine learning", "ml", "predict", "prediccion", "predicción", "modelo", "singleton"],
    },
    "dashboard": {
        "label": "Dashboard del proyecto",
        "description": "Resumen funcional del tablero Streamlit y sus módulos financieros.",
        "keywords": ["dashboard", "tablero", "aplicacion", "aplicación", "proyecto", "que hace", "qué hace"],
    },
    "stress": {
        "label": "Stress testing",
        "description": "Escenarios adversos con shocks de mercado, tasas y volatilidad.",
        "keywords": ["stress", "stress testing", "escenario adverso", "escenarios", "shock", "caida de mercado", "caída de mercado"],
    },
}

CHATBOT_ALLOWED_FINANCIAL_MODULES = set(CHATBOT_FINANCIAL_TOPIC_CATALOG.keys()) | {
    "risk",
    "portfolio",
    "valuation",
    "macro",
    "ml",
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
    "bono",
    "renta fija",
    "vencimiento",
    "cupon",
    "cupón",
    "precio limpio",
    "precio sucio",
    "yield",
    "dv01",
    "cartera",
    "correlacion",
    "correlación",
    "diversificacion",
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
    "dashboard",
    "tablero",
    "proyecto",
    "horizonte",
    "backtesting",
    "excedencias",
    "violaciones",
    "distribucion",
    "distribución",
    "gaussiana",
    "gausiana",
    "gaussiaana",
    "normal",
    "student",
    "t student",
    "series de tiempo",
}


def get_financial_topic_keys() -> list[str]:
    return sorted(CHATBOT_FINANCIAL_TOPIC_CATALOG.keys())


def get_financial_keywords() -> set[str]:
    return set(CHATBOT_ALLOWED_FINANCIAL_KEYWORDS)


def get_financial_modules() -> set[str]:
    return set(CHATBOT_ALLOWED_FINANCIAL_MODULES)
