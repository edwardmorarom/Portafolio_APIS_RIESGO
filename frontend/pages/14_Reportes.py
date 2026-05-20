from __future__ import annotations

import pandas as pd
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_ui import header_dashboard, nota, seccion, tarjeta_kpi
from ui.page_setup import setup_dashboard_page


modo, filtros_panel = setup_dashboard_page(
    title="Reportes",
    subtitle="Universidad Santo Tomás",
    filtros_label="Parámetros de reporte",
    filtros_expanded=False,
    page_title="Reportes",
    page_icon="📄",
)

client = get_api_client()

with filtros_panel:
    st.caption("Reporte ejecutivo institucional PDF-ready.")

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
    tarjeta_kpi("Proyecto", "Riesgo USTA", subtexto=str(report.get("project", "N/D")))
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
    "Este reporte funciona como base ejecutiva para documentar KYC, riesgo, optimización, ML, chatbot y arquitectura técnica."
)

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
