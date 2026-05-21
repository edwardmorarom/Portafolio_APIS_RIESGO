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

    En la siguiente subtarea este payload se conectará con la configuración global
    del portafolio y con resultados reales guardados en session_state/frontend.
    """
    overrides = overrides or {}
    portfolio_context = overrides.get("portfolio_context") or {
        "tickers": "Pendiente de selección global del usuario",
        "horizon": "Pendiente de horizonte global",
        "weights": "Pendiente de asignación inicial",
        "base_currency": "USD",
        "risk_profile": "Pendiente de perfil KYC",
        "perri_reference": "Pendiente de portafolio Perri sugerido",
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
        "var_portfolio": "Pendiente de conectar resultado real de VaR/CVaR",
        "markowitz_optimal": "Pendiente de conectar composición óptima Markowitz",
        "jensen_alpha": "Pendiente de conectar alpha de Jensen/CAPM",
        "ml_performance": "Pendiente de conectar predicción o métrica ML",
        "stress_loss": "Pendiente de conectar pérdida bajo escenario de estrés",
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

    sections = overrides.get("sections") or [
        {"title": "1. Resumen ejecutivo", "description": "Síntesis del portafolio seleccionado, horizonte, pesos, benchmark y principales lecturas de riesgo."},
        {"title": "2. Composición del portafolio y países", "description": "Lista de activos, país de origen, tipo de activo, benchmark metodológico y pesos definidos por el usuario."},
        {
            "title": "3. Benchmark y justificación",
            "description": (
                f"Benchmark aplicado: {benchmark_context.get('ticker', portfolio_context.get('benchmark', 'N/D'))}. "
                f"{benchmark_context.get('explanation', benchmark_context.get('reason', 'Se define automáticamente según la composición del portafolio.'))}"
            ),
        },
        {"title": "4. Rendimientos, volatilidad, VaR/CVaR y Kupiec", "description": "Consolida retorno, volatilidad, VaR histórico, paramétrico y Monte Carlo, CVaR complementario y validación Kupiec cuando exista."},
        {"title": "5. CAPM, Markowitz y eficiencia", "description": "Incluye beta, alpha de Jensen, retorno esperado CAPM, frontera eficiente, Sharpe y lectura de eficiencia frente al benchmark."},
        {"title": "6. Stress testing", "description": "Resume escenario base, escenarios adversos, pérdida estimada del portafolio y comparación defensiva contra el benchmark."},
        {"title": "7. Renta fija y opciones", "description": "Documenta curva de tasas, duración, convexidad, valoración Black-Scholes y Greeks cuando el análisis aplique."},
        {"title": "8. Machine Learning", "description": "Explica variable objetivo, features, modelo persistido con joblib, patrón Singleton, endpoint /predict, métricas, supuestos y limitaciones."},
        {"title": "9. Tests, Docker, deploy y CI", "description": "Evidencia pytest + TestClient, Docker multi-stage, docker-compose, GitHub Actions y preparación para deploy PaaS."},
        {"title": "10. Conclusiones y recomendaciones", "description": "Las recomendaciones se derivan del perfil KYC, los resultados de riesgo, la comparación contra benchmark y la robustez bajo estrés."},
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
