from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_chip_row, render_info_card, render_meta_row
from ui.dashboard_ui import header_dashboard, nota, seccion, tarjeta_kpi
from ui.page_setup import setup_dashboard_page
from ui.theme import build_global_css, image_to_base64, safe_text


USERS_PATH = Path("backend/data/users.json")
LOGO_PATH = "frontend/assets/escudo_santo_tomas.png"

MODULE_GROUPS = {
    "Mercado y contexto": [
        ("Módulo 0", "Contextualización", "Universo de activos, moneda, Rf y benchmark.", "pages/0_Contextualizacion.py"),
        ("Módulo 1", "Técnico", "Precio, medias móviles, RSI, Bollinger, MACD y estocástico.", "pages/01_Tecnico.py"),
        ("Módulo 2", "Rendimientos", "Distribución, normalidad, QQ plot y estadística descriptiva.", "pages/02_Rendimientos.py"),
        ("Módulo 8", "Macro y benchmark", "Tasa libre de riesgo, FX, alpha, tracking error e IR.", "pages/08_Macro_Benchmark.py"),
    ],
    "Riesgo cuantitativo": [
        ("Módulo 3", "GARCH", "ARCH, GARCH, EGARCH, diagnóstico y pronóstico de volatilidad.", "pages/03_Garch.py"),
        ("Módulo 4", "CAPM", "Beta, alpha, retorno esperado y lectura por activo o portafolio.", "pages/04_Capm.py"),
        ("Módulo 5", "VaR/CVaR", "VaR histórico, paramétrico, Monte Carlo, CVaR y Kupiec.", "pages/05_Var_Cvar.py"),
        ("Módulo 11", "Stress testing", "Escenarios adversos de tasa, mercado y volatilidad.", "pages/11_Stress_Testing.py"),
    ],
    "Optimización y modelos": [
        ("Módulo 6", "Markowitz", "Frontera eficiente, mínimos, Sharpe y comparación Perri.", "pages/06_Markowitz.py"),
        ("Módulo 7", "Señales", "Lectura integrada de señales técnicas por activo.", "pages/07_Señales.py"),
        ("Módulo 9", "Renta fija", "Nelson-Siegel, curva de tasas, duración y convexidad.", "pages/09_Renta_Fija.py"),
        ("Módulo 10", "Opciones", "Black-Scholes, Greeks, payoff y sensibilidad.", "pages/10_Opciones.py"),
        ("Módulo 12", "Machine Learning", "Predicción de retorno con variables de riesgo y mercado.", "pages/12_Machine_Learning.py"),
    ],
}


def _init_session_state() -> None:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_name = None


def _load_users() -> list[dict]:
    if not USERS_PATH.exists():
        return []

    with USERS_PATH.open("r", encoding="utf-8-sig") as file:
        payload = json.load(file)

    users = payload.get("users", [])
    return users if isinstance(users, list) else []


def verificar_login(username: str, password: str) -> bool:
    for user in _load_users():
        if user.get("username") == username and user.get("password") == password:
            st.session_state.logged_in = True
            st.session_state.user_role = user.get("role", "user")
            st.session_state.user_name = user.get("full_name", username)
            return True

    return False


def _logout() -> None:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.rerun()


def _role_label(role: str | None) -> str:
    return "Superusuario" if role == "superuser" else "Cliente"


def _login_css() -> str:
    return """
    <style>
        .stApp {
            background:
                radial-gradient(circle at 16% 10%, rgba(56, 189, 248, 0.20), transparent 25%),
                radial-gradient(circle at 88% 20%, rgba(37, 99, 235, 0.24), transparent 26%),
                linear-gradient(135deg, #06122F 0%, #071536 48%, #04102A 100%) !important;
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="collapsedControl"] {
            display: none !important;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.2rem;
        }

        div[data-testid="stForm"] {
            background: rgba(8, 24, 58, 0.68) !important;
            border: 1px solid rgba(180, 218, 255, 0.18) !important;
            border-radius: 22px !important;
            padding: 1.1rem !important;
            box-shadow: 0 24px 55px rgba(0, 0, 0, 0.26) !important;
            backdrop-filter: blur(18px);
        }

        div[data-testid="stForm"] label,
        div[data-testid="stForm"] p {
            color: #D8E6FF !important;
        }

        div[data-testid="stForm"] input {
            background: rgba(255,255,255,0.08) !important;
            border: 1px solid rgba(255,255,255,0.24) !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }

        .login-card-header {
            background: rgba(8, 24, 58, 0.68);
            border: 1px solid rgba(180, 218, 255, 0.18);
            border-radius: 22px;
            padding: 1.1rem 1.1rem 0.85rem 1.1rem;
            margin-bottom: 0.7rem;
            box-shadow: 0 18px 44px rgba(0, 0, 0, 0.20);
            backdrop-filter: blur(18px);
        }
    </style>
    """


def _logo_html() -> str:
    logo_b64 = image_to_base64(LOGO_PATH)
    if not logo_b64:
        return '<div class="login-logo"></div>'
    return f'<img class="login-logo" src="data:image/png;base64,{logo_b64}" alt="USTA">'


def _render_login() -> None:
    st.set_page_config(
        page_title="Acceso | Portafolio Riesgo USTA",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(build_global_css("General"), unsafe_allow_html=True)
    st.markdown(_login_css(), unsafe_allow_html=True)

    left, right = st.columns([1.12, 0.88], gap="large")

    with left:
        st.markdown(
            f"""
            <div class="login-stage">
                <div class="login-glow one"></div>
                <div class="login-glow two"></div>
                <div class="login-brand" style="position:relative;z-index:1;">
                    {_logo_html()}
                    <div>
                        <div class="login-brand-title">Portafolio Riesgo USTA</div>
                        <div class="login-brand-subtitle">RoboAdvisor institucional</div>
                    </div>
                </div>
                <div class="login-title" style="position:relative;z-index:1;margin-top:4.2rem;">Welcome back...</div>
                <div class="login-subtitle" style="position:relative;z-index:1;">
                    Riesgo, valoración, optimización y automatización Perri en un entorno financiero profesional.
                </div>
                <div class="login-trust-row" style="position:relative;z-index:1;">
                    <span class="login-trust">FastAPI</span>
                    <span class="login-trust">Streamlit</span>
                    <span class="login-trust">SQLite</span>
                    <span class="login-trust">Perri</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="login-card-header">
                <div class="login-card-title">Sign in</div>
                <div class="login-card-subtitle">Ingresa con tus credenciales asignadas.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Contraseña")
            submitted = st.form_submit_button("Ingresar", use_container_width=True)

            if submitted:
                if verificar_login(username.strip(), password):
                    st.success(f"Bienvenido, {st.session_state.user_name}.")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

    st.stop()


def _render_module_card(module: tuple[str, str, str, str]) -> None:
    code, title, description, page_path = module
    st.markdown(
        f"""
        <div class="module-card">
            <div class="module-card-kicker">{safe_text(code)}</div>
            <div class="module-card-title">{safe_text(title)}</div>
            <div class="module-card-body">{safe_text(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link(page_path, label=f"Abrir {title}", use_container_width=True)


def _render_modules_tab() -> None:
    group_tabs = st.tabs(list(MODULE_GROUPS.keys()))

    for tab, (_, modules) in zip(group_tabs, MODULE_GROUPS.items()):
        with tab:
            for row_start in range(0, len(modules), 2):
                cols = st.columns(2, gap="large")
                for col, module in zip(cols, modules[row_start:row_start + 2]):
                    with col:
                        _render_module_card(module)


def _render_status_tab() -> None:
    client = get_api_client()

    try:
        root = client.get_root()
        health = client.get_health()
        system = client.get("/system/status")

        c1, c2, c3 = st.columns(3)
        with c1:
            tarjeta_kpi("Backend", str(health.get("status", "N/D")).upper(), subtexto="FastAPI")
        with c2:
            tarjeta_kpi("Versión", str(root.get("version", system.get("app_version", "N/D"))), subtexto="API")
        with c3:
            tarjeta_kpi("ML", "Activo" if system.get("ml_enabled") else "Inactivo", subtexto=system.get("ml_model_version", "N/D"))

        render_meta_row(
            {
                "Entorno": health.get("env", "N/D"),
                "Prefijo API": system.get("api_prefix", "/api/v1"),
                "Chatbot": f"{system.get('chatbot_provider', 'local')} · {system.get('chatbot_model', 'N/D')}",
            }
        )
    except ApiClientError as exc:
        st.warning(f"No fue posible consultar el backend: {exc.message}")
    except Exception as exc:
        st.warning(f"No fue posible consultar el backend: {exc}")


def _render_session_tab() -> None:
    role = st.session_state.get("user_role")

    left, right = st.columns([1.05, 1.0], gap="large")
    with left:
        st.markdown(
            f"""
            <div class="session-panel">
                <div class="session-panel-title">Sesión activa</div>
                <div class="session-panel-body">
                    Usuario: <strong>{safe_text(st.session_state.get("user_name"))}</strong><br>
                    Rol: <strong>{safe_text(_role_label(role))}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_chip_row(["Streamlit", "FastAPI", "SQLite", "Perri", "ML"])

    with right:
        render_info_card(
            "Alcance del rol",
            (
                "El cliente accede a lectura, simulación y análisis. El superusuario queda preparado para flujos "
                "administrativos como auditoría KYC, reserva de activos y gestión institucional."
            ),
        )
        if st.button("Cerrar sesión", key="home_logout", use_container_width=True):
            _logout()


def _render_home() -> None:
    modo, filtros_panel = setup_dashboard_page(
        title="Dashboard Riesgo",
        subtitle="Universidad Santo Tomás",
        filtros_label="Parámetros generales",
        filtros_expanded=False,
        page_title="Dashboard Riesgo",
        page_icon="📊",
    )

    with filtros_panel:
        st.caption("Panel de inicio")
        st.write("Usa las pestañas superiores para navegar por módulos y este panel para opciones generales.")

    header_dashboard(
        "Centro de análisis de portafolio",
        "Riesgo, valoración, optimización, señales y automatización institucional en una sola experiencia.",
        modo=modo,
    )

    role = st.session_state.get("user_role")
    render_meta_row(
        {
            "Usuario": st.session_state.get("user_name", "N/D"),
            "Rol": _role_label(role),
            "Interfaz": "Diseño profesional",
            "Modo": modo,
        }
    )

    tab_home, tab_modules, tab_status, tab_session = st.tabs(
        ["Resumen", "Módulos", "Estado", "Sesión"]
    )

    with tab_home:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            tarjeta_kpi("Cobertura", "13", subtexto="Módulos Streamlit")
        with c2:
            tarjeta_kpi("Backend", "FastAPI", subtexto="Servicios financieros")
        with c3:
            tarjeta_kpi("Perri", "1y · 3y · 5y", subtexto="Horizontes institucionales")
        with c4:
            tarjeta_kpi("Modelo", "ML", subtexto="Predicción de retorno")

        seccion("Flujo recomendado")
        cols = st.columns(3, gap="large")
        with cols[0]:
            render_info_card("1. Contexto", "Revisa activos, moneda, tasa libre de riesgo y benchmark.")
        with cols[1]:
            render_info_card("2. Riesgo", "Evalúa volatilidad, CAPM, VaR/CVaR, GARCH y stress testing.")
        with cols[2]:
            render_info_card("3. Decisión", "Contrasta Markowitz, señales, Perri, RoboAdvisor y ML.")

        if role == "superuser":
            nota("Modo superusuario activo: el diseño queda preparado para paneles de auditoría, KYC y gestión institucional.")
        else:
            nota("Modo cliente activo: navegación enfocada en consulta, simulación y lectura financiera.")

    with tab_modules:
        _render_modules_tab()

    with tab_status:
        _render_status_tab()

    with tab_session:
        _render_session_tab()


_init_session_state()

if not st.session_state.logged_in:
    _render_login()

_render_home()
