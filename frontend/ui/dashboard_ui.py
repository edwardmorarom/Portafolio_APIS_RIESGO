from __future__ import annotations
from html import escape

import streamlit as st

from ui.theme import build_global_css, image_to_base64, safe_text


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


def render_sidebar_panel(
    modo_default: str = "General",
    filtros_label: str = "Opciones Del Módulo",
    filtros_expanded: bool = False,
):
    expander = st.sidebar.expander("Filtros Del Módulo", expanded=True)

    with expander:
        st.markdown(
            '<div style="font-size:0.92rem;font-weight:700;color:var(--accent-main);margin:0.15rem 0 0.45rem 0;">Modo De Visualización</div>',
            unsafe_allow_html=True,
        )

        modo = st.radio(
            "Modo De Visualización",
            ["General", "Estadístico"],
            index=0 if modo_default == "General" else 1,
            key="sidebar_modo_visualizacion",
            label_visibility="collapsed",
            help="General resume e interpreta. Estadístico profundiza más en lectura técnica y detalle analítico.",
        )

        inner_expander = st.expander(filtros_label, expanded=filtros_expanded)

    return modo, inner_expander


def mode_badge(modo: str):
    st.markdown(
        f'<span class="ui-mode-badge">Modo {safe_text(modo)}</span>',
        unsafe_allow_html=True,
    )


def header_dashboard(titulo: str, subtitulo: str, modo: str | None = None):
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


def plot_card_header(titulo: str, help_text: str, modo: str = "General", caption: str = ""):
    caption_html = f'<div class="ui-plot-caption">{safe_text(caption)}</div>' if caption else ""

    st.markdown(
        f"""
        <div class="ui-plot-head">
            <div class="ui-plot-head-top">
                <div style="display:flex;align-items:center;gap:0.30rem;margin:0;">
                    <div class="ui-plot-title">{safe_text(titulo)}</div>
                    <span class="ui-help" title="{safe_text(help_text)}">?</span>
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