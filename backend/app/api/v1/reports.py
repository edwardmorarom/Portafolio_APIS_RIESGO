from __future__ import annotations

from datetime import date

from fastapi import APIRouter

router = APIRouter()


@router.get("/executive-summary", summary="Resumen ejecutivo institucional PDF-ready")
def get_executive_summary() -> dict:
    return {
        "report_title": "Reporte Ejecutivo de Riesgo - Portafolio USTA",
        "generated_at": date.today().isoformat(),
        "institution": "Universidad Santo Tomas",
        "project": "Proyecto Integrador de Riesgo",
        "sections": [
            {
                "title": "Perfil del inversionista",
                "description": "El sistema incorpora un flujo KYC para sugerir perfiles conservador, moderado o agresivo.",
            },
            {
                "title": "Riesgo de mercado",
                "description": "El proyecto calcula VaR, CVaR, CAPM, beta, alpha, GARCH y stress testing.",
            },
            {
                "title": "Optimizacion de portafolio",
                "description": "Markowitz y Perri permiten construir portafolios optimizados por riesgo, Sharpe y perfil.",
            },
            {
                "title": "Machine Learning",
                "description": "El modulo ML predice retorno esperado a partir de volatilidad, Sharpe, VaR, beta y mercado.",
            },
            {
                "title": "Chatbot experto",
                "description": "El chatbot combina motor experto local con proveedor externo Gemini y fallback seguro.",
            },
        ],
        "technical_stack": [
            "FastAPI",
            "Pydantic",
            "SQLAlchemy",
            "SQLite",
            "Streamlit",
            "Docker",
            "GitHub Actions",
            "pytest",
        ],
        "status": "PDF_READY",
    }
