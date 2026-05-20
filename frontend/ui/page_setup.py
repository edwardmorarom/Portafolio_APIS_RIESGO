from __future__ import annotations

import streamlit as st
from ui.dashboard_ui import (
    aplicar_estilos_globales,
    render_filter_panel,
    render_top_navigation,
)


def setup_dashboard_page(
    title: str = "Dashboard Riesgo",
    subtitle: str = "Universidad Santo Tomás",
    logo_path: str = "frontend/assets/escudo_santo_tomas.png",
    modo_default: str = "General",
    filtros_label: str = "Parámetros Del Módulo",
    filtros_expanded: bool = False,
    page_title: str | None = None,
    page_icon: str | None = None,
):
    # --- CAPA DE SEGURIDAD GLOBAL ---
    # Protege todas las páginas de la carpeta 'pages/'
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.switch_page("app.py")
    # --------------------------------

    try:
        st.set_page_config(
            page_title=page_title or title,
            page_icon=page_icon,
            layout="wide",
        )
    except st.errors.StreamlitAPIException:
        pass

    aplicar_estilos_globales(modo="General")

    render_top_navigation()

    modo, filtros_panel = render_filter_panel(
        modo_default=modo_default,
        filtros_label=filtros_label,
        filtros_expanded=filtros_expanded,
    )

    aplicar_estilos_globales(modo=modo)

    return modo, filtros_panel
