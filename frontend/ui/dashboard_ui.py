from __future__ import annotations
from html import escape

import streamlit as st

from ui.theme import build_global_css, image_to_base64, safe_text


NAV_ITEMS = [
    ("Inicio", "app.py"),
    ("0 Contexto", "pages/0_Contextualizacion.py"),
    ("1 Técnico", "pages/01_Tecnico.py"),
    ("2 Rendimientos", "pages/02_Rendimientos.py"),
    ("3 GARCH", "pages/03_Garch.py"),
    ("4 CAPM", "pages/04_Capm.py"),
    ("5 VaR/CVaR", "pages/05_Var_Cvar.py"),
    ("6 Markowitz", "pages/06_Markowitz.py"),
    ("7 Señales", "pages/07_Señales.py"),
    ("8 Macro", "pages/08_Macro_Benchmark.py"),
    ("9 Renta fija", "pages/09_Renta_Fija.py"),
    ("10 Opciones", "pages/10_Opciones.py"),
    ("11 Stress", "pages/11_Stress_Testing.py"),
    ("12 ML", "pages/12_Machine_Learning.py"),
]


def aplicar_estilos_globales(modo: str = "General"):
    st.markdown(build_global_css(modo), unsafe_allow_html=True)


def render_sidebar_brand(
    title: str = "Dashboard Riesgo",
    subtitle: str = "Universidad Santo Tomás",
    logo_path: str = "frontend/assets/escudo_santo_tomas.png",
):
    logo_b64 = image_to_base64(logo_path)

    if logo_b64:
        logo_html = f'<img class="sidebar-brand-logo" src="data:image/png;base64,{logo_b64}" alt="Logo">'
    else:
        logo_html = (
            '<div class="sidebar-brand-logo" '
            'style="display:flex;align-items:center;justify-content:center;'
            'font-weight:800;color:var(--accent-main);">LOGO</div>'
        )

    st.sidebar.markdown(
        f"""
        <div class="sidebar-brand-wrap">
            <div class="sidebar-brand">
                <div class="sidebar-brand-inner">
                    {logo_html}
                    <div>
                        <div class="sidebar-brand-title">{safe_text(title)}</div>
                        <div class="sidebar-brand-subtitle">{safe_text(subtitle)}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_session():
    if not st.session_state.get("logged_in"):
        return

    user_name = st.session_state.get("user_name") or "Usuario"
    role = st.session_state.get("user_role") or "user"
    role_label = "Superusuario" if role == "superuser" else "Cliente"

    st.sidebar.markdown(
        f"""
        <div class="sidebar-session">
            <div class="sidebar-session-name">{safe_text(user_name)}</div>
            <div class="sidebar-session-role">{safe_text(role_label)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Cerrar sesión", key="sidebar_logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.switch_page("app.py")


def render_sidebar_panel(
    modo_default: str = "General",
    filtros_label: str = "Opciones Del Módulo",
    filtros_expanded: bool = False,
):
    st.sidebar.markdown(
        '<div style="font-size:0.92rem;font-weight:700;color:var(--accent-main);margin:0.15rem 0 0.45rem 0;">Modo De Visualización</div>',
        unsafe_allow_html=True,
    )

    modo = st.sidebar.radio(
        "Modo De Visualización",
        ["General", "Estadístico"],
        index=0 if modo_default == "General" else 1,
        key="sidebar_modo_visualizacion",
        label_visibility="collapsed",
        help="General resume e interpreta. Estadístico profundiza más en lectura técnica y detalle analítico.",
    )

    filtros_sidebar = st.sidebar.expander(filtros_label, expanded=filtros_expanded)

    return modo, filtros_sidebar


def render_top_navigation():
    user_name = st.session_state.get("user_name") or "Usuario"
    role = st.session_state.get("user_role") or "user"
    role_label = "Superusuario" if role == "superuser" else "Cliente"

    st.markdown(
        f"""
        <div class="top-shell">
            <div>
                <div class="top-brand">Portafolio Riesgo USTA</div>
                <div class="top-subtitle">Riesgo cuantitativo, valoración y optimización institucional</div>
            </div>
            <div class="top-session">
                <span>{safe_text(user_name)}</span>
                <strong>{safe_text(role_label)}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="nav-ordered-label">Navegación de módulos</div>', unsafe_allow_html=True)

    items_per_row = 7
    for start in range(0, len(NAV_ITEMS), items_per_row):
        row_items = NAV_ITEMS[start:start + items_per_row]
        cols = st.columns(len(row_items))
        for col, (label, page_path) in zip(cols, row_items):
            with col:
                st.page_link(page_path, label=label, use_container_width=True)


def render_filter_panel(
    modo_default: str = "General",
    filtros_label: str = "Parámetros Del Módulo",
    filtros_expanded: bool = False,
):
    panel = st.expander(filtros_label, expanded=filtros_expanded)

    with panel:
        modo = st.radio(
            "Modo de visualización",
            ["General", "Estadístico"],
            index=0 if modo_default == "General" else 1,
            key="top_modo_visualizacion",
            horizontal=True,
            help="General resume e interpreta. Estadístico prioriza detalle técnico y lectura cuantitativa.",
        )

    return modo, panel


def mode_badge(modo: str):
    st.markdown(
        f'<span class="ui-mode-badge">Modo {safe_text(modo)}</span>',
        unsafe_allow_html=True,
    )


def header_dashboard(
    titulo: str | None = None,
    subtitulo: str | None = None,
    modo: str | None = None,
    **kwargs,
):
    if titulo is None:
        titulo = kwargs.pop("title", "")
    if subtitulo is None:
        subtitulo = kwargs.pop("subtitle", "")

    badge_html = f'<span class="ui-mode-badge">Modo {safe_text(modo)}</span>' if modo else ""

    st.markdown(
        f"""
        <div class="ui-hero">
            <div class="ui-hero-top">
                <h1 style="margin:0;">{safe_text(titulo)}</h1>
                {badge_html}
            </div>
            <p style="margin:0.15rem 0 0 0;">{safe_text(subtitulo)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nota(texto: str):
    st.markdown(
        f'<div class="ui-note">{safe_text(texto)}</div>',
        unsafe_allow_html=True,
    )


def seccion(titulo: str):
    st.markdown(
        f"""
        <h2>{safe_text(titulo)}</h2>
        <hr class="ui-divider">
        """,
        unsafe_allow_html=True,
    )


def titulo_con_ayuda(titulo: str, help_text: str, nivel: int = 3):
    tag = "h2" if nivel == 2 else "h3"
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:0.30rem;margin-bottom:0.25rem;">
            <{tag} style="margin:0;">{safe_text(titulo)}</{tag}>
            <span class="ui-help" title="{safe_text(help_text)}">?</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def tarjeta_kpi(
    titulo: str,
    valor: str,
    delta: str = "",
    help_text: str = "",
    subtexto: str = "",
):
    delta_class = "neu"
    if str(delta).startswith("+"):
        delta_class = "pos"
    elif str(delta).startswith("-"):
        delta_class = "neg"

    titulo_safe = safe_text(titulo)
    valor_safe = safe_text(valor)
    delta_safe = safe_text(delta)
    help_safe = safe_text(help_text)
    subtexto_safe = safe_text(subtexto)

    help_html = f'<span class="ui-help" title="{help_safe}">?</span>' if help_safe else ""
    delta_html = f'<div class="ui-kpi-delta {delta_class}">{delta_safe}</div>' if delta_safe else ""
    subtexto_html = f'<div class="ui-kpi-sub">{subtexto_safe}</div>' if subtexto_safe else ""

    card_html = (
        '<div class="ui-kpi-card">'
        '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:0.5rem;margin-bottom:0.55rem;">'
        f'<div class="ui-kpi-title">{titulo_safe}</div>'
        f'{help_html}'
        '</div>'
        f'<div class="ui-kpi-value">{valor_safe}</div>'
        f'{delta_html}'
        f'{subtexto_html}'
        '</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)


def plot_card_header(titulo: str, help_text: str = "", modo: str = "General", caption: str = ""):
    caption_html = f'<div class="ui-plot-caption">{safe_text(caption)}</div>' if caption else ""
    help_html = f'<span class="ui-help" title="{safe_text(help_text)}">?</span>' if help_text else ""

    st.markdown(
        f"""
        <div class="ui-plot-head">
            <div class="ui-plot-head-top">
                <div style="display:flex;align-items:center;gap:0.30rem;margin:0;">
                    <div class="ui-plot-title">{safe_text(titulo)}</div>
                    {help_html}
                </div>
                <span class="ui-mode-badge">Modo {safe_text(modo)}</span>
            </div>
            {caption_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def plot_card_footer(texto: str):
    st.markdown(
        f'<div class="ui-plot-foot">{safe_text(texto)}</div>',
        unsafe_allow_html=True,
    )


def toolbar_label(texto: str):
    st.markdown(
        f'<div class="ui-toolbar-label">{safe_text(texto)}</div>',
        unsafe_allow_html=True,
    )
