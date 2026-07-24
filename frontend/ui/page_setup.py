from __future__ import annotations

import inspect
from pathlib import Path

import streamlit as st
from ui.chatbot_widget import render_floating_chatbot
from ui.dashboard_ui import (
    aplicar_estilos_globales,
    render_invisible_filter_panel,
    render_sidebar_brand,
    render_sidebar_session,
    render_top_navigation,
)


HIDDEN_FOR_ALL_USERS = {
    "11_Stress_Testing.py",
    "12_Machine_Learning.py",
    "13_Perfil_Riesgo.py",
}


def _current_page_name() -> str:
    page_names = {
        "app.py",
        "0_Contextualizacion.py",
        "01_Tecnico.py",
        "02_Rendimientos.py",
        "03_Garch.py",
        "04_Capm.py",
        "05_Var_Cvar.py",
        "06_Markowitz.py",
        "07_Señales.py",
        "08_Macro_Benchmark.py",
        "09_Renta_Fija.py",
        "10_Opciones.py",
        "11_Stress_Testing.py",
        "12_Machine_Learning.py",
        "13_Perfil_Riesgo.py",
        "14_Reportes.py",
        "15_Usuarios.py",
    }

    for frame in inspect.stack():
        candidate = Path(frame.filename).name
        if candidate in page_names:
            return candidate

    return "app.py"


def _has_active_portfolio() -> bool:
    config = st.session_state.get("portfolio_config", {}) or {}
    return bool(config.get("tickers"))


def setup_dashboard_page(
    title: str = "P.R.ED",
    subtitle: str = "Desarrolla Tus Portafolios",
    logo_path: str = "frontend/assets/pred_dachshund_logo.png",
    modo_default: str = "General",
    filtros_label: str = "Parámetros del módulo",
    filtros_expanded: bool = False,
    page_title: str | None = None,
    page_icon: str | None = None,
):
    # --- CAPA DE SEGURIDAD GLOBAL ---
    # Protege todas las páginas de la carpeta 'pages/'
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.switch_page("app.py")
    # --------------------------------

    current_page = _current_page_name()
    if current_page in HIDDEN_FOR_ALL_USERS:
        st.warning("Este módulo está oculto temporalmente.")
        st.switch_page("app.py")

    if current_page == "15_Usuarios.py" and st.session_state.get("user_role") != "superuser":
        st.warning("Este módulo solo está habilitado para superusuarios.")
        st.switch_page("app.py")

    if current_page != "app.py" and not _has_active_portfolio():
        if current_page == "15_Usuarios.py":
            pass
        else:
            st.warning("Primero debes seleccionar o crear un portafolio desde Inicio.")
            st.switch_page("app.py")

    try:
        st.set_page_config(
            page_title=page_title or title,
            page_icon=page_icon,
            layout="wide",
        )
    except st.errors.StreamlitAPIException:
        pass

    aplicar_estilos_globales(modo="General")

    render_sidebar_brand(title=title, subtitle=subtitle, logo_path=logo_path)
    render_sidebar_session()

    render_top_navigation()

    modo, filtros_panel = render_invisible_filter_panel(
        filtros_label=filtros_label,
        filtros_expanded=filtros_expanded,
    )

    aplicar_estilos_globales(modo=modo)
    render_floating_chatbot(module=title, mode=modo)

    return modo, filtros_panel
