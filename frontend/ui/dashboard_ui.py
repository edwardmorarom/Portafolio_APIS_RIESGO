from __future__ import annotations
from contextlib import nullcontext
from html import escape
import json
from pathlib import Path
import streamlit as st

from ui.theme import build_global_css, image_to_base64, safe_text
from ui.formatting import (
    DEFAULT_DECIMALS,
    MAX_DECIMALS,
    apply_decimal_display_options,
    format_percent,
    patch_streamlit_dataframe_locale,
)


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
    ("13 Perfil", "pages/13_Perfil_Riesgo.py"),
]


def _navigation_items() -> list[tuple[str, str]]:
    items = [
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
        ("13 Perfil", "pages/13_Perfil_Riesgo.py"),
    ]
    if st.session_state.get("user_role") == "superuser":
        items.append(("Admin Usuarios", "pages/15_Usuarios.py"))
    return items


NAV_ITEMS = _navigation_items()


def aplicar_estilos_globales(modo: str = "General"):
    apply_decimal_display_options()
    patch_streamlit_dataframe_locale()
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







def _persist_user_session_data(
    *,
    username: str,
    full_name: str,
    kyc_data: dict,
) -> tuple[bool, str]:
    users_path = Path(__file__).resolve().parents[2] / "backend" / "data" / "users.json"

    username = str(username or "").strip().lower()
    full_name = str(full_name or "").strip()

    if not username or username == "n/d":
        return False, "No se encontr el username de la sesin. Cierra sesin e ingresa nuevamente."

    if not users_path.exists():
        return False, f"No existe el archivo de usuarios: {users_path}"

    try:
        payload = json.loads(users_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, f"No fue posible leer users.json: {exc}"

    users = payload.get("users", [])
    if not isinstance(users, list):
        return False, "users.json no tiene una lista vlida de usuarios."

    user_found = None
    for user in users:
        current_username = str(user.get("username", "")).strip().lower()
        if current_username == username:
            user_found = user
            break

    if user_found is None:
        return False, f"No se encontr el usuario '{username}' en users.json."

    if full_name:
        user_found["full_name"] = full_name

    current_kyc = user_found.get("kyc", {}) or {}

    current_kyc["age"] = int(kyc_data.get("age", current_kyc.get("age", 30)))
    current_kyc["experience"] = int(kyc_data.get("experience", current_kyc.get("experience", 0)))

    user_found["kyc"] = current_kyc

    try:
        users_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
    except Exception as exc:
        return False, f"No fue posible guardar users.json: {exc}"

    return True, "Datos personales guardados correctamente."


def render_sidebar_session():
    if not st.session_state.get("logged_in"):
        return

    user_name = st.session_state.get("user_name") or "Usuario"
    username = st.session_state.get("user_username") or "N/D"
    role = st.session_state.get("user_role") or "user"
    role_label = "Superusuario" if role == "superuser" else "Cliente"

    user_kyc = st.session_state.get("user_kyc_data", {}) or {}
    portfolio_config = st.session_state.get("portfolio_config", {}) or {}

    profile = (
        st.session_state.get("kyc_profile")
        or portfolio_config.get("risk_profile")
        or user_kyc.get("fallback_profile")
        or "pendiente"
    )

    age = int(user_kyc.get("age", 30))
    experience = int(user_kyc.get("experience", 2))

    tickers = portfolio_config.get("tickers", []) or []
    weights = portfolio_config.get("weights_pct", []) or []
    horizon = portfolio_config.get("horizon_type") or "PENDIENTE"
    base_currency = portfolio_config.get("base_currency", "USD")

    st.sidebar.markdown(
        f"""
        <div class="sidebar-profile-card">
            <div class="sidebar-profile-title">Mi usuario</div>
            <div class="sidebar-profile-grid">
                <div class="sidebar-profile-item">
                    <span class="sidebar-profile-label">Nombre</span>
                    <strong class="sidebar-profile-value">{safe_text(user_name)}</strong>
                </div>
                <div class="sidebar-profile-item">
                    <span class="sidebar-profile-label">Usuario</span>
                    <strong class="sidebar-profile-value">{safe_text(username)}</strong>
                </div>
                <div class="sidebar-profile-item">
                    <span class="sidebar-profile-label">Rol</span>
                    <strong class="sidebar-profile-value">{safe_text(role_label)}</strong>
                </div>
                <div class="sidebar-profile-item">
                    <span class="sidebar-profile-label">Perfil de riesgo</span>
                    <strong class="sidebar-profile-value">{safe_text(str(profile).upper())}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.divider()

    with st.sidebar.expander("Configurar datos personales", expanded=False):
        st.caption("Estos datos actualizan la sesin actual y se guardan en el registro del usuario.")

        with st.form("sidebar_personal_data_form"):
            new_full_name = st.text_input(
                "Nombre completo",
                value=str(user_name),
                key="sidebar_user_full_name",
            )

            new_age = st.number_input(
                "Edad",
                min_value=18,
                max_value=150,
                value=age,
                step=1,
                key="sidebar_user_age",
            )

            new_experience = st.number_input(
                "Experiencia invirtiendo",
                min_value=0,
                max_value=100,
                value=experience,
                step=1,
                key="sidebar_user_experience",
            )

            submitted = st.form_submit_button(
                "Guardar datos personales",
                use_container_width=True,
            )

            if submitted:
                updated_kyc = dict(user_kyc)
                updated_kyc["age"] = int(new_age)
                updated_kyc["experience"] = int(new_experience)

                ok, message = _persist_user_session_data(
                    username=username,
                    full_name=new_full_name,
                    kyc_data=updated_kyc,
                )

                st.session_state.user_name = new_full_name
                st.session_state.user_kyc_data = updated_kyc

                if ok:
                    st.success(message)
                else:
                    st.warning(message)

                st.rerun()

    st.sidebar.divider()

    st.sidebar.subheader("Portafolio activo")

    c1, c2 = st.sidebar.columns(2)
    with c1:
        st.metric("Activos", len(tickers))
    with c2:
        st.metric("Moneda", base_currency)

    st.sidebar.markdown(
        f"""
        <div class="sidebar-portfolio-summary">
            <div class="sidebar-portfolio-summary-title">Resumen de riesgo</div>
            <div class="sidebar-portfolio-summary-grid">
                <div class="sidebar-portfolio-summary-item">
                    <span>Riesgo asumido</span>
                    <strong>{safe_text(str(profile).upper())}</strong>
                </div>
                <div class="sidebar-portfolio-summary-item">
                    <span>Horizonte</span>
                    <strong>{safe_text(str(horizon).upper())}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if tickers:
        with st.sidebar.expander("Ver tickers y pesos", expanded=False):
            for index, ticker in enumerate(tickers):
                weight = weights[index] if index < len(weights) else None
                if weight is None:
                    st.write(f"- {ticker}")
                else:
                    st.write(f"- {ticker}: {format_percent(weight, already_pct=True)}")
    else:
        st.caption("An no hay portafolio global guardado.")

    apply_decimal_display_options()

    st.sidebar.divider()

    st.sidebar.number_input(
        "Decimales visuales",
        min_value=0,
        max_value=MAX_DECIMALS,
        value=int(st.session_state.get("display_decimals", DEFAULT_DECIMALS)),
        step=1,
        key="display_decimals",
        help="Solo cambia el formato mostrado en KPIs, tablas y reportes; no altera los cálculos internos.",
    )

    apply_decimal_display_options()

    st.sidebar.divider()

    if st.sidebar.button("Cerrar sesin", key="sidebar_logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.session_state.user_username = None
        st.session_state.user_kyc_data = {}
        st.session_state.user_preferred_horizon = None
        st.session_state.portfolio_config = {}
        st.session_state.robo_portfolio = []
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
    import inspect
    from pathlib import Path as _Path

    nav_items = [
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
        ("13 Perfil", "pages/13_Perfil_Riesgo.py"),
    ]

    nav_items = _navigation_items()
    page_names = {_Path(page_path).name for _, page_path in nav_items}
    current_name = "app.py"

    for frame in inspect.stack():
        candidate = _Path(frame.filename).name
        if candidate in page_names:
            current_name = candidate
            break

    st.markdown(
        """
        <style>
            .top-nav-active-pill {
                width: 100%;
                min-height: 2.55rem;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                border-radius: 999px;
                padding: 0.45rem 0.70rem;
                background: linear-gradient(135deg, #8A1538 0%, #B91C1C 100%);
                color: #FFFFFF !important;
                -webkit-text-fill-color: #FFFFFF !important;
                font-size: 0.82rem;
                font-weight: 900;
                line-height: 1.2;
                box-shadow: 0 8px 20px rgba(138, 21, 56, 0.22);
                border: 1px solid rgba(255,255,255,0.20);
                margin-bottom: 0.18rem;
            }

            .top-nav-active-caption {
                color: #64748B !important;
                -webkit-text-fill-color: #64748B !important;
                font-size: 0.68rem;
                font-weight: 800;
                text-align: center;
                margin-bottom: 0.22rem;
            }

            [data-testid="stPageLink"] a {
                min-height: 2.55rem !important;
                border-radius: 999px !important;
                font-weight: 850 !important;
                text-align: center !important;
                white-space: normal !important;
                line-height: 1.2 !important;
                padding: 0.48rem 0.62rem !important;
                overflow: visible !important;
            }

            [data-testid="stPageLink"] p {
                white-space: normal !important;
                line-height: 1.2 !important;
                text-align: center !important;
                overflow-wrap: normal !important;
                word-break: keep-all !important;
            }

            .top-nav-locked-pill {
                width: 100%;
                min-height: 2.55rem;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                border-radius: 999px;
                padding: 0.45rem 0.70rem;
                background: rgba(148, 163, 184, 0.10);
                color: #94A3B8 !important;
                -webkit-text-fill-color: #94A3B8 !important;
                font-size: 0.82rem;
                font-weight: 850;
                line-height: 1.2;
                border: 1px solid rgba(148, 163, 184, 0.22);
                opacity: 0.72;
                cursor: not-allowed;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    portfolio_ready = bool((st.session_state.get("portfolio_config", {}) or {}).get("tickers"))

    # 15 módulos en 3 filas de 5 para que el texto no quede apretado.
    for row_start in range(0, len(nav_items), 5):
        cols = st.columns(5, gap="small")
        row_items = nav_items[row_start:row_start + 5]

        for col, (label, page_path) in zip(cols, row_items):
            page_name = _Path(page_path).name

            with col:
                if page_name == current_name:
                    st.markdown(
                        f"""
                        <div class="top-nav-active-pill">{safe_text(label)}</div>
                        <div class="top-nav-active-caption">Actual</div>
                        """,
                        unsafe_allow_html=True,
                    )
                elif not portfolio_ready and page_name not in {"app.py", "15_Usuarios.py"}:
                    st.markdown(
                        f'<div class="top-nav-locked-pill" title="Configura un portafolio en Inicio">{safe_text(label)}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.page_link(
                        page_path,
                        label=label,
                        use_container_width=True,
                    )


def render_invisible_filter_panel(
    filtros_label: str | None = "Filtros del módulo",
    filtros_expanded: bool = False,
):
    """
    Panel tcnico vaco para mantener compatibilidad con pginas que hacen:

        modo, filtros_sidebar = setup_dashboard_page(...)
        with filtros_sidebar:
            ...

    Muestra filtros en un panel compacto para no ocupar espacio cuando no se usan.
    """
    if filtros_label is None:
        return "General", nullcontext()

    panel = st.expander(f"Mostrar filtros / Ocultar filtros · {filtros_label}", expanded=filtros_expanded)
    return "General", panel


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
            <span class="ui-help" title="{safe_text(help_text)}"></span>
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

    help_html = f'<span class="ui-help" title="{help_safe}"></span>' if help_safe else ""
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
    help_html = f'<span class="ui-help" title="{safe_text(help_text)}"></span>' if help_text else ""

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

