from __future__ import annotations

import pandas as pd
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_ui import header_dashboard, nota, seccion, tarjeta_kpi
from ui.formatting import format_percent
from ui.page_setup import setup_dashboard_page
from ui.portfolio_state import (
    active_assets,
    active_benchmark,
    active_benchmark_details,
    active_config,
    active_horizon_label,
    active_tickers,
    active_weights_pct,
)


def _current_report_payload(mode: str, custom_notes: str = "") -> dict:
    config = active_config()
    assets = active_assets()
    tickers = active_tickers()
    weights = active_weights_pct()
    benchmark = active_benchmark_details()

    composition = []
    for index, ticker in enumerate(tickers):
        asset = assets[index] if index < len(assets) else {}
        weight = weights[index] if index < len(weights) else None
        composition.append(
            {
                "ticker": ticker,
                "name": asset.get("name", ticker),
                "country": asset.get("country", "N/D"),
                "asset_type": asset.get("asset_type", "N/D"),
                "weight": format_percent(weight, already_pct=True) if weight is not None else "N/D",
                "benchmark": benchmark["ticker"],
            }
        )

    key_results = {
        "composicion": "; ".join(f"{row['ticker']} {row['weight']}" for row in composition) or "N/D",
        "benchmark": f"{benchmark['ticker']} - {benchmark.get('reason', '')}",
        "rendimientos": "Usar resultado calculado en módulo 2 si está disponible en la sesión.",
        "volatilidad": "Usar resultado calculado en módulos 2/3 si está disponible en la sesión.",
        "var_cvar_kupiec": "Usar tabla comparativa del módulo 5; no se inventan cifras si no han sido calculadas.",
        "capm": "Usar beta, alpha y retorno esperado del módulo 4.",
        "markowitz": "Usar frontera eficiente y portafolio óptimo del módulo 6.",
        "stress": "Usar pérdida estimada y comparación contra benchmark del módulo 11.",
        "renta_fija_opciones": "Usar curva, duración, convexidad, Black-Scholes y Greeks cuando aplique.",
        "machine_learning": "Usar predicción del endpoint /ml/predict y métricas del modelo.",
    }

    sections = [
        {
            "title": "1. Riesgo financiero y hallazgos",
            "description": (
                f"El riesgo financiero es la posibilidad de pérdidas por mercado, volatilidad, tasas o eventos extremos. "
                f"Portafolio: {', '.join(tickers) or 'N/D'}. Horizonte: {active_horizon_label()}. Benchmark: {benchmark['ticker']}."
            ),
        },
        {
            "title": "2. Decisiones metodológicas",
            "description": (
                "Los activos provienen de la configuración inicial; el benchmark se define automáticamente por composición. "
                "GARCH se usa para volatilidad condicional; VaR histórico, paramétrico y Monte Carlo para pérdida de cola; "
                "ML predice retorno acumulado como apoyo analítico, no como recomendación automática."
            ),
        },
        {
            "title": "3. Arquitectura técnica",
            "description": (
                "Cinco capas: frontend Streamlit, backend FastAPI, contratos Pydantic/servicios financieros, "
                "persistencia SQLAlchemy/SQLite y capa ML con Singleton. Docker, deploy y CI evidencian operación técnica."
            ),
        },
        {
            "title": "4. Resultados numéricos clave",
            "description": (
                f"VaR/Kupiec: {key_results['var_cvar_kupiec']} "
                f"Markowitz: {key_results['markowitz']} "
                f"CAPM/alpha: {key_results['capm']} "
                f"ML: {key_results['machine_learning']} "
                f"Stress: {key_results['stress']} "
                "No se inventan cifras no calculadas."
            ),
        },
        {
            "title": "5. Conclusiones y recomendaciones",
            "description": custom_notes or (
                "La decisión de inversión debe depender del perfil KYC, la eficiencia frente al benchmark, "
                "el balance retorno-riesgo, la pérdida bajo estrés y la consistencia de los modelos."
            ),
        },
    ]

    return {
        "portfolio_context": {
            "tickers": ", ".join(tickers) or "N/D",
            "weights": ", ".join(row["weight"] for row in composition) or "N/D",
            "horizon": active_horizon_label(),
            "benchmark": benchmark["ticker"],
            "benchmark_reason": benchmark.get("reason", "N/D"),
            "base_currency": config.get("base_currency", "USD"),
            "risk_profile": config.get("risk_profile", "N/D"),
        },
        "benchmark_context": benchmark,
        "key_results": key_results,
        "sections": sections,
    }


modo, filtros_panel = setup_dashboard_page(
    title="Reportes",
    subtitle="Desarrolla Tus Portafolios",
    filtros_label="Parámetros de reporte",
    filtros_expanded=False,
    page_title="Reportes",
    page_icon="📄",
)

client = get_api_client()

with filtros_panel:
    report_mode = st.radio(
        "Fuente del reporte",
        ["Usar elecciones actuales del dashboard", "Ingresar datos nuevos para el reporte"],
        horizontal=True,
        key="report_source_mode",
    )
    custom_notes = ""
    if report_mode == "Ingresar datos nuevos para el reporte":
        custom_notes = st.text_area(
            "Conclusiones / recomendaciones para el PDF",
            placeholder="Ej: El portafolio muestra perfil defensivo frente al benchmark...",
            key="report_custom_notes",
        )
    st.caption(
        f"Portafolio activo: {', '.join(active_tickers()) or 'N/D'} · "
        f"Horizonte: {active_horizon_label()} · Benchmark: {active_benchmark()}"
    )

header_dashboard(
    "Reportes ejecutivos",
    "Consolida el estado institucional del proyecto para entrega, sustentación y futura generación PDF.",
    modo=modo,
)

try:
    report = client.get_executive_summary_report()
except ApiClientError as exc:
    st.error(f"No fue posible cargar el reporte: {exc.message}")
    st.stop()
except Exception as exc:
    st.error(f"Error inesperado cargando reporte: {exc}")
    st.stop()

seccion("Resumen institucional")

c1, c2, c3 = st.columns(3)

with c1:
    tarjeta_kpi("Estado", str(report.get("status", "N/D")), subtexto="Preparado para PDF")
with c2:
    tarjeta_kpi("Proyecto", "P.R.ED", subtexto=str(report.get("project", "N/D")))
with c3:
    tarjeta_kpi("Fecha", str(report.get("generated_at", "N/D")), subtexto="Generación")

render_meta_row(
    {
        "Título": report.get("report_title", "N/D"),
        "Institución": report.get("institution", "N/D"),
        "Stack": " · ".join(report.get("technical_stack", [])),
    }
)

nota(
    "Este reporte consolida la configuración actual del portafolio y deja explícito que Docker/deploy/CI corresponden al criterio 13 de la rúbrica."
)

pdf_payload = _current_report_payload(report_mode, custom_notes)
try:
    pdf_bytes = client.build_executive_summary_pdf(pdf_payload)
    st.download_button(
        "Descargar PDF ejecutivo",
        data=pdf_bytes,
        file_name="reporte_riesgo_usta.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )
except Exception as exc:
    st.warning(f"No fue posible preparar el PDF personalizado: {exc}")

seccion("Secciones del reporte")

sections = report.get("sections", [])
if sections:
    df_sections = pd.DataFrame(sections)
    st.dataframe(df_sections, use_container_width=True, hide_index=True)

    for item in sections:
        render_info_card(
            str(item.get("title", "Sección")),
            str(item.get("description", "")),
        )
else:
    render_info_card("Sin secciones", "El backend no devolvió secciones para el reporte.")
