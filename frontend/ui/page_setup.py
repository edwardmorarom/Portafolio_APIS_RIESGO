from __future__ import annotations

import streamlit as st

from config import APP_SUBTITLE, APP_TITLE, USTA_LOGO
from ui.dashboard_ui import (
    aplicar_estilos_globales,
    render_sidebar_brand,
    render_sidebar_navigation,
    render_sidebar_panel,
)


def setup_dashboard_page(
    title: str = APP_TITLE,
    subtitle: str = APP_SUBTITLE,
    logo_path: str = USTA_LOGO,
    modo_default: str = "General",
    filtros_label: str = "Parámetros Del Módulo",
    filtros_expanded: bool = True,
):
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "sidebar_modo_visualizacion" not in st.session_state:
        st.session_state["sidebar_modo_visualizacion"] = modo_default

    aplicar_estilos_globales(st.session_state["sidebar_modo_visualizacion"])

    render_sidebar_brand(
        title=title,
        subtitle=subtitle,
        logo_path=logo_path,
    )

    render_sidebar_navigation()

    modo, filtros_sidebar = render_sidebar_panel(
        modo_default=st.session_state["sidebar_modo_visualizacion"],
        filtros_label=filtros_label,
        filtros_expanded=filtros_expanded,
    )

    aplicar_estilos_globales(modo=modo)

    return modo, filtros_sidebar