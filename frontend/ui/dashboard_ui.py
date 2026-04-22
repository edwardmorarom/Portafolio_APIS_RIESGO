from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


def _safe(text: str | None) -> str:
    return "" if text is None else str(text)


def _image_to_base64(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode()


def _theme_tokens(modo: str = "General") -> dict:
    if modo == "Estadístico":
        return {
            "app_bg_start": "#FCFCFD",
            "app_bg_end": "#FFF7FA",
            "text_main": "#0F172A",
            "text_soft": "#334155",
            "text_muted": "#64748B",
            "accent_main": "#9F1239",
            "accent_second": "#BE123C",
            "accent_soft": "rgba(190, 24, 93, 0.10)",
            "accent_border": "rgba(190, 24, 93, 0.20)",
            "panel_alt": "#FFF8FA",
            "sidebar_bg_1": "#8B0D35",
            "sidebar_bg_2": "#6D0E2D",
            "sidebar_text": "#FDF2F8",
            "border_soft": "rgba(148, 163, 184, 0.20)",
            "shadow": "0 10px 28px rgba(15, 23, 42, 0.08)",
            "active_nav_text": "#8B0D35",
        }

    return {
        "app_bg_start": "#FCFCFD",
        "app_bg_end": "#F6FAFF",
        "text_main": "#0F172A",
        "text_soft": "#334155",
        "text_muted": "#64748B",
        "accent_main": "#1D4ED8",
        "accent_second": "#2563EB",
        "accent_soft": "rgba(37, 99, 235, 0.10)",
        "accent_border": "rgba(37, 99, 235, 0.20)",
        "panel_alt": "#F8FBFF",
        "sidebar_bg_1": "#0B3A8C",
        "sidebar_bg_2": "#0A3279",
        "sidebar_text": "#EFF6FF",
        "border_soft": "rgba(148, 163, 184, 0.20)",
        "shadow": "0 10px 28px rgba(15, 23, 42, 0.08)",
        "active_nav_text": "#1D4ED8",
    }


def aplicar_estilos_globales(modo: str = "General"):
    t = _theme_tokens(modo)

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background:
                radial-gradient(circle at top right, {t["accent_soft"]}, transparent 24%),
                linear-gradient(180deg, {t["app_bg_start"]} 0%, {t["app_bg_end"]} 100%);
        }}

        .block-container {{
            padding-top: 1.1rem;
            max-width: 1340px;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: {t["text_main"]} !important;
            opacity: 1 !important;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {t["sidebar_bg_1"]} 0%, {t["sidebar_bg_2"]} 100%);
            border-right: 1px solid rgba(255,255,255,0.08);
        }}

        [data-testid="stSidebar"] * {{
            color: {t["sidebar_text"]} !important;
        }}

        [data-testid="stSidebarNav"] {{
            display: none !important;
        }}

        .sidebar-brand-wrap {{
            margin-bottom: 1rem;
        }}

        .sidebar-brand {{
            background: #FFFFFF;
            border: 1px solid rgba(255,255,255,0.72);
            border-radius: 22px;
            padding: 1rem 1rem 0.95rem 1rem;
            box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        }}

        .sidebar-brand-inner {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }}

        .sidebar-brand-logo {{
            width: 62px;
            height: 62px;
            border-radius: 50%;
            object-fit: contain;
            flex-shrink: 0;
        }}

        .sidebar-brand-title {{
            font-size: 1.2rem;
            line-height: 1.0;
            font-weight: 900;
            color: {t["accent_main"]} !important;
            margin: 0;
        }}

        .sidebar-brand-subtitle {{
            font-size: 0.82rem;
            color: #334155 !important;
            margin-top: 0.25rem;
            font-weight: 600;
        }}

        .sidebar-nav-card {{
            margin-top: 0.9rem;
            margin-bottom: 1rem;
        }}

        .sidebar-nav-title {{
            font-size: 0.82rem;
            font-weight: 900;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: #DBEAFE !important;
            margin-bottom: 0.7rem;
            padding-left: 0.15rem;
        }}

        div[data-testid="stPageLink"] {{
            margin-bottom: 0.5rem;
        }}

        div[data-testid="stPageLink"] a {{
            background: rgba(255,255,255,0.10) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 16px !important;
            padding: 0.9rem 1rem !important;
            min-height: 50px !important;
            display: flex !important;
            align-items: center !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
            transition: all 0.18s ease !important;
        }}

        div[data-testid="stPageLink"] a:hover {{
            background: rgba(255,255,255,0.16) !important;
            transform: translateY(-1px);
        }}

        div[data-testid="stPageLink"] a p,
        div[data-testid="stPageLink"] a span,
        div[data-testid="stPageLink"] a div {{
            color: #EFF6FF !important;
            font-weight: 800 !important;
            font-size: 0.98rem !important;
        }}

        div[data-testid="stPageLinkCurrent"] a,
        div[data-testid="stPageLink"] a[aria-current="page"] {{
            background: #FFFFFF !important;
            border: 1px solid rgba(255,255,255,0.85) !important;
            box-shadow: 0 8px 18px rgba(0,0,0,0.12) !important;
        }}

        div[data-testid="stPageLinkCurrent"] a p,
        div[data-testid="stPageLinkCurrent"] a span,
        div[data-testid="stPageLinkCurrent"] a div,
        div[data-testid="stPageLink"] a[aria-current="page"] p,
        div[data-testid="stPageLink"] a[aria-current="page"] span,
        div[data-testid="stPageLink"] a[aria-current="page"] div {{
            color: {t["active_nav_text"]} !important;
            font-weight: 900 !important;
        }}

        /* expander principal */
        [data-testid="stSidebar"] .streamlit-expanderHeader {{
            background: #FFFFFF !important;
            border: 1px solid rgba(255,255,255,0.75) !important;
            border-radius: 18px !important;
            padding: 0.9rem 1rem !important;
            font-weight: 900 !important;
            color: {t["accent_main"]} !important;
            box-shadow: 0 8px 18px rgba(0,0,0,0.10);
        }}

        [data-testid="stSidebar"] details > div {{
            background: #FFFFFF !important;
            border: 1px solid rgba(255,255,255,0.75) !important;
            border-top: none !important;
            border-bottom-left-radius: 18px !important;
            border-bottom-right-radius: 18px !important;
            padding: 1rem 1rem 0.9rem 1rem !important;
            box-shadow: 0 8px 18px rgba(0,0,0,0.10);
            margin-top: -3px;
        }}

        [data-testid="stSidebar"] details > div *,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stCaption {{
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
            opacity: 1 !important;
        }}

        [data-testid="stSidebar"] .stRadio > div {{
            background: #F8FAFC;
            border: 1px solid rgba(148,163,184,0.25);
            border-radius: 18px;
            padding: 0.75rem 0.9rem;
            margin-top: 0.45rem;
            margin-bottom: 0.65rem;
        }}

        [data-testid="stSidebar"] .stSelectbox > div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] .stTextInput input,
        [data-testid="stSidebar"] .stNumberInput input,
        [data-testid="stSidebar"] .stDateInput input {{
            background: #FFFFFF !important;
            border: 1px solid rgba(148,163,184,0.28) !important;
            border-radius: 14px !important;
            color: #0F172A !important;
            font-weight: 600 !important;
        }}

        /* expander interno: AHORA CLARO */
        [data-testid="stSidebar"] details details summary {{
            background: #F8FAFC !important;
            border: 1px solid rgba(148,163,184,0.25) !important;
            border-radius: 14px !important;
            color: #0F172A !important;
            padding: 0.75rem 0.9rem !important;
            font-weight: 800 !important;
        }}

        [data-testid="stSidebar"] details details > div {{
            background: #FFFFFF !important;
            border: 1px solid rgba(148,163,184,0.20) !important;
            border-top: none !important;
            border-radius: 0 0 14px 14px !important;
            padding: 0.9rem 0.9rem 0.8rem 0.9rem !important;
            box-shadow: none !important;
            margin-top: -2px !important;
        }}

        [data-testid="stSidebar"] details details > div *,
        [data-testid="stSidebar"] details details .stMarkdown,
        [data-testid="stSidebar"] details details .stMarkdown p,
        [data-testid="stSidebar"] details details .stCaption {{
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
            opacity: 1 !important;
        }}

        .ui-note {{
            background: linear-gradient(180deg, #FFFFFF 0%, {t["panel_alt"]} 100%);
            padding: 0.95rem 1rem;
            border-left: 4px solid {t["accent_main"]};
            border-radius: 16px;
            margin-bottom: 1rem;
            border: 1px solid {t["border_soft"]};
            box-shadow: {t["shadow"]};
            color: {t["text_soft"]} !important;
            line-height: 1.65;
        }}

        .ui-hero {{
            background: linear-gradient(135deg, #FFFFFF 0%, {t["panel_alt"]} 100%);
            padding: 1.45rem 1.5rem;
            border-radius: 22px;
            margin-bottom: 1rem;
            border: 1px solid {t["accent_border"]};
            box-shadow: {t["shadow"]};
        }}

        .ui-hero-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.8rem;
            flex-wrap: wrap;
            margin-bottom: 0.25rem;
        }}

        .ui-mode-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 34px;
            padding: 0.42rem 0.92rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 900;
            color: #FFFFFF !important;
            background: linear-gradient(135deg, {t["accent_main"]}, {t["accent_second"]});
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.14);
            white-space: nowrap;
        }}

        .section-heading {{
            font-size: 1.2rem;
            font-weight: 900;
            color: {t["text_main"]} !important;
            margin-top: 1rem;
            margin-bottom: 0.7rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand(
    title: str = "Dashboard Riesgo",
    subtitle: str = "Universidad Santo Tomás",
    logo_path: str = "frontend/assets/escudo_santo_tomas.png",
):
    logo_b64 = _image_to_base64(logo_path)

    if logo_b64:
        logo_html = f'<img class="sidebar-brand-logo" src="data:image/png;base64,{logo_b64}" alt="Escudo">'
    else:
        logo_html = '<div class="sidebar-brand-logo" style="display:flex;align-items:center;justify-content:center;font-weight:800;color:#1D4ED8;">USTA</div>'

    st.sidebar.markdown(
        f"""
        <div class="sidebar-brand-wrap">
            <div class="sidebar-brand">
                <div class="sidebar-brand-inner">
                    {logo_html}
                    <div>
                        <div class="sidebar-brand-title">{_safe(title)}</div>
                        <div class="sidebar-brand-subtitle">{_safe(subtitle)}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_navigation():
    st.sidebar.markdown('<div class="sidebar-nav-card">', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-nav-title">App</div>', unsafe_allow_html=True)
    st.sidebar.page_link("app.py", label="Inicio")
    st.sidebar.page_link("pages/0_Contextualizacion.py", label="Contextualización")
    st.sidebar.markdown("</div>", unsafe_allow_html=True)


def render_sidebar_panel(
    modo_default: str = "General",
    filtros_label: str = "Opciones Del Módulo",
    filtros_expanded: bool = True,
):
    expander = st.sidebar.expander("Filtros Del Módulo", expanded=True)

    with expander:
        st.markdown("### Modo De Visualización")
        modo = st.radio(
            "Modo De Visualización",
            ["General", "Estadístico"],
            index=0 if modo_default == "General" else 1,
            key="sidebar_modo_visualizacion",
            label_visibility="collapsed",
        )
        inner_expander = st.expander(filtros_label, expanded=filtros_expanded)

    return modo, inner_expander


def header_dashboard(titulo: str, subtitulo: str, modo: str | None = None):
    badge_html = f'<span class="ui-mode-badge">Modo {_safe(modo)}</span>' if modo else ""
    st.markdown(
        f"""
        <div class="ui-hero">
            <div class="ui-hero-top">
                <h1 style="margin:0;">{_safe(titulo)}</h1>
                {badge_html}
            </div>
            <p style="margin:0.2rem 0 0 0; color:#334155;">{_safe(subtitulo)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nota(texto: str):
    st.markdown(f'<div class="ui-note">{_safe(texto)}</div>', unsafe_allow_html=True)


def seccion(titulo: str):
    st.markdown(f'<div class="section-heading">{_safe(titulo)}</div>', unsafe_allow_html=True)