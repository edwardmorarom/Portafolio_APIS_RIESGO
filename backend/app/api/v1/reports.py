from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse

from app.services.pdf_service import build_executive_pdf


router = APIRouter()


def build_report_payload(overrides: dict[str, Any] | None = None) -> dict:
    """
    Payload ejecutivo base del reporte.

    Esta versión deja el PDF alineado con la rúbrica:
    1. Riesgo financiero y hallazgos.
    2. Decisiones metodológicas.
    3. Arquitectura técnica en 5 capas.
    4. Resultados numéricos clave.
    5. Conclusiones y recomendaciones.

    El frontend puede enviar overrides con los resultados reales calculados en la
    sesion. Si falta una metrica, se marca como no calculada para no inventar datos.
    """
    overrides = overrides or {}
    portfolio_context = overrides.get("portfolio_context") or {
        "tickers": "No informado por el dashboard",
        "horizon": "No informado por el dashboard",
        "weights": "No informado por el dashboard",
        "base_currency": "USD",
        "risk_profile": "No informado por el dashboard",
        "perri_reference": "No informado por el dashboard",
    }
    benchmark_context = overrides.get("benchmark_context") or {}

    methodology_decisions = [
        {
            "decision": "Selección de activos",
            "detail": (
                "Los activos deben provenir de la configuración inicial del usuario, "
                "con máximo 15 tickers y análisis en moneda base USD."
            ),
        },
        {
            "decision": "Modelo GARCH",
            "detail": (
                "El módulo compara ARCH(1), GARCH(1,1) y EGARCH(1,1). "
                "Actualmente selecciona el mejor modelo por AIC y reporta AIC/BIC."
            ),
        },
        {
            "decision": "Método de VaR",
            "detail": (
                "El análisis incorpora VaR/CVaR histórico, paramétrico y Monte Carlo, "
                "junto con backtesting Kupiec para validar calibración."
            ),
        },
        {
            "decision": "Propósito analítico del ML",
            "detail": (
                "El modelo ML estima retorno esperado usando variables de riesgo y mercado: "
                "volatilidad, Sharpe, VaR, beta y retorno de mercado."
            ),
        },
    ]

    architecture_layers = [
        {
            "layer": "Frontend",
            "detail": "Dashboard Streamlit modular con navegación por páginas financieras.",
        },
        {
            "layer": "Backend",
            "detail": "API FastAPI con routers v1, servicios financieros y contratos Pydantic.",
        },
        {
            "layer": "Base de datos",
            "detail": "SQLite y SQLAlchemy para persistencia de activos, precios y datos institucionales.",
        },
        {
            "layer": "Machine Learning",
            "detail": "Predictor Singleton con modelo joblib y endpoint de predicción.",
        },
        {
            "layer": "Reportes y deploy",
            "detail": "Generación PDF con ReportLab, Docker, CI/CD y despliegue frontend/backend.",
        },
    ]

    key_results = {
        "var_portfolio": "No calculado en esta sesion",
        "markowitz_optimal": "No calculado en esta sesion",
        "jensen_alpha": "No calculado en esta sesion",
        "ml_performance": "No calculado en esta sesion",
        "stress_loss": "No calculado en esta sesion",
    }
    key_results.update(overrides.get("key_results") or {})

    conclusions = [
        (
            "El portafolio debe evaluarse de forma integrada: rendimiento, volatilidad, "
            "VaR/CVaR, beta, alpha, stress testing y predicción ML."
        ),
        (
            "La recomendación final debe depender del perfil KYC: conservador, moderado "
            "o agresivo, evitando sugerencias iguales para inversionistas distintos."
        ),
        (
            "Perri debe usarse como referencia institucional para comparar portafolios "
            "precalculados de 5, 10 y 15 activos."
        ),
    ]

    requested_sections = overrides.get("sections")
    sections = requested_sections[:5] if isinstance(requested_sections, list) and requested_sections else [
        {
            "title": "1. Riesgo financiero y hallazgos",
            "description": (
                "El riesgo financiero es la posibilidad de pérdidas por cambios en mercado, volatilidad, tasas, "
                "liquidez o eventos extremos. Este reporte resume solo hallazgos calculados o declarados por el dashboard: "
                f"portafolio {portfolio_context.get('tickers', 'N/D')}, horizonte {portfolio_context.get('horizon', 'N/D')} "
                f"y benchmark {benchmark_context.get('ticker', portfolio_context.get('benchmark', 'N/D'))}."
            ),
        },
        {
            "title": "2. Decisiones metodológicas",
            "description": (
                "Los activos se toman de la selección inicial del usuario y sus pesos; el benchmark se define por composición "
                "geográfica. GARCH se usa para volatilidad condicional, VaR histórico/paramétrico/Monte Carlo para pérdidas de cola "
                "y ML como apoyo predictivo de retorno acumulado, no como prueba causal."
            ),
        },
        {
            "title": "3. Arquitectura técnica",
            "description": (
                "La solución se organiza en cinco capas: frontend Streamlit, backend FastAPI, contratos Pydantic/servicios, "
                "persistencia SQLAlchemy/SQLite y capa ML con modelo cargado por Singleton. Docker, CI y deploy evidencian operación técnica."
            ),
        },
        {
            "title": "4. Resultados numéricos clave",
            "description": (
                "Se reportan únicamente métricas disponibles: VaR del portafolio, composición óptima Markowitz, alpha de Jensen, "
                "performance o predicción ML y pérdida bajo estrés. Si una cifra aparece como N/D o pendiente, no fue calculada en la sesión."
            ),
        },
        {
            "title": "5. Conclusiones y recomendaciones",
            "description": (
                "La recomendación debe derivarse del perfil KYC, del balance retorno-riesgo, de la eficiencia frente al benchmark, "
                "del comportamiento bajo estrés y de la coherencia de los modelos. No se recomienda invertir solo por una métrica aislada."
            ),
        },
    ]

    return {
        "report_title": "Reporte Ejecutivo de Riesgo - Portafolio USTA",
        "generated_at": date.today().isoformat(),
        "institution": "Universidad Santo Tomás",
        "project": "Proyecto Integrador de Riesgo",
        "status": "PDF_EXECUTIVE_READY",
        "portfolio_context": portfolio_context,
        "sections": sections,
        "methodology_decisions": methodology_decisions,
        "architecture_layers": architecture_layers,
        "key_results": key_results,
        "conclusions": conclusions,
        "technical_stack": [
            "FastAPI",
            "Pydantic",
            "SQLAlchemy",
            "SQLite",
            "Streamlit",
            "ReportLab",
            "Machine Learning",
            "Docker",
            "GitHub Actions",
            "pytest",
        ],
    }


@router.get("/executive-summary", summary="Resumen ejecutivo institucional PDF-ready")
def get_executive_summary() -> dict:
    return build_report_payload()


@router.get("/executive-summary/pdf", summary="Descargar reporte ejecutivo PDF")
def download_executive_summary_pdf():
    payload = build_report_payload()
    pdf_bytes = build_executive_pdf(payload)

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=reporte_riesgo_usta.pdf"
        },
    )


@router.post("/executive-summary/pdf", summary="Generar reporte ejecutivo PDF con contexto del dashboard")
def download_custom_executive_summary_pdf(payload: dict[str, Any] = Body(default_factory=dict)):
    report_payload = build_report_payload(payload)
    pdf_bytes = build_executive_pdf(report_payload)

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=reporte_riesgo_usta_personalizado.pdf"
        },
    )
