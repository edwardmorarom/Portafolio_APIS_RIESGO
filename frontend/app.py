from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_chip_row, render_info_card, render_meta_row
from ui.dashboard_ui import header_dashboard, nota, seccion, tarjeta_kpi
from ui.page_setup import setup_dashboard_page
from ui.portfolio_config import render_global_portfolio_config
from ui.theme import build_global_css, image_to_base64, safe_text


USERS_PATH = Path("backend/data/users.json")
LOGO_PATH = "frontend/assets/pred_dachshund_logo.png"

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
    ],
    "Optimización y modelos": [
        ("Módulo 6", "Markowitz", "Frontera eficiente, mínimos, Sharpe y comparación Perri.", "pages/06_Markowitz.py"),
        ("Módulo 7", "Señales", "Lectura integrada de señales técnicas por activo.", "pages/07_Señales.py"),
        ("Módulo 9", "Renta fija", "Nelson-Siegel, curva de tasas, duración y convexidad.", "pages/09_Renta_Fija.py"),
        ("Módulo 10", "Opciones", "Black-Scholes, Greeks, payoff y sensibilidad.", "pages/10_Opciones.py"),
    ],
}


def _init_session_state() -> None:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_name = None
    if "display_decimals" not in st.session_state:
        st.session_state.display_decimals = 2
    if "show_register_panel" not in st.session_state:
        st.session_state.show_register_panel = False
    if "login_prefill_username" not in st.session_state:
        st.session_state.login_prefill_username = ""
    if "user_has_recovery_code" not in st.session_state:
        st.session_state.user_has_recovery_code = True


def _load_users() -> list[dict]:
    if not USERS_PATH.exists():
        return []

    with USERS_PATH.open("r", encoding="utf-8-sig") as file:
        payload = json.load(file)

    users = payload.get("users", [])
    return users if isinstance(users, list) else []


def _users_json_path() -> Path:
    return Path("backend/data/users.json")


def _load_users_for_registration() -> list[dict]:
    users_path = _users_json_path()

    if not users_path.exists():
        return []

    payload = json.loads(users_path.read_text(encoding="utf-8-sig"))
    users = payload.get("users", [])

    return users if isinstance(users, list) else []


def _save_users_for_registration(users: list[dict]) -> None:
    users_path = _users_json_path()
    users_path.parent.mkdir(parents=True, exist_ok=True)
    users_path.write_text(
        json.dumps({"users": users}, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )


def _username_exists_for_registration(username: str) -> bool:
    username = str(username or "").strip().lower()

    return any(
        str(user.get("username", "")).strip().lower() == username
        for user in _load_users_for_registration()
    )


def _normalise_recovery_code(recovery_code: str) -> str:
    return "".join(str(recovery_code or "").upper().split())


def _normalise_recovery_code_state(key: str) -> None:
    st.session_state[key] = _normalise_recovery_code(st.session_state.get(key, ""))


def _recovery_code_error(recovery_code: str) -> str | None:
    recovery_code = _normalise_recovery_code(recovery_code)

    if len(recovery_code) < 6:
        return "La clave de recuperación debe tener mínimo 6 caracteres."

    if not any(char.isalpha() for char in recovery_code) or not any(char.isdigit() for char in recovery_code):
        return "**La clave de recuperación debe combinar letras y números.** Ejemplo: 20/FEB/2003."

    return None


def actualizar_password_por_recuperacion(
    *,
    username: str,
    recovery_code: str,
    new_password: str,
) -> tuple[bool, str]:
    username = str(username or "").strip().lower()
    recovery_code = _normalise_recovery_code(recovery_code)
    new_password = str(new_password or "")

    if len(username) < 4:
        return False, "Ingresa un usuario válido."

    code_error = _recovery_code_error(recovery_code)
    if code_error:
        return False, code_error

    if len(new_password) < 6:
        return False, "La nueva contraseña debe tener mínimo 6 caracteres."

    users = _load_users_for_registration()

    for user in users:
        current_username = str(user.get("username", "")).strip().lower()
        current_recovery_code = _normalise_recovery_code(user.get("recovery_code", ""))

        if current_username != username:
            continue

        if not current_recovery_code:
            return False, "Esta cuenta no tiene clave de recuperación registrada."

        if current_recovery_code != recovery_code:
            return False, "La clave de recuperación no coincide."

        user["password"] = new_password
        _save_users_for_registration(users)
        return True, "Contraseña actualizada. Ya puedes ingresar con tu nueva contraseña."

    return False, "No encontramos ese usuario."


def actualizar_clave_recuperacion_usuario(username: str, recovery_code: str) -> tuple[bool, str]:
    username = str(username or "").strip().lower()
    recovery_code = _normalise_recovery_code(recovery_code)

    code_error = _recovery_code_error(recovery_code)
    if code_error:
        return False, code_error

    users = _load_users_for_registration()

    for user in users:
        current_username = str(user.get("username", "")).strip().lower()
        if current_username != username:
            continue

        user["recovery_code"] = recovery_code
        _save_users_for_registration(users)
        return True, "Clave de recuperación guardada correctamente."

    return False, "No encontramos el usuario activo."


def _risk_profile_from_registration(age: int, experience: int, tolerance: int, objective: str) -> str:
    score = 0

    if age <= 30:
        score += 1
    elif age >= 60:
        score -= 1

    if experience >= 5:
        score += 1
    elif experience <= 1:
        score -= 1

    if tolerance >= 4:
        score += 2
    elif tolerance <= 2:
        score -= 2

    if objective == "preservacion_capital":
        score -= 1
    elif objective == "crecimiento":
        score += 1

    if score <= -2:
        return "conservador"

    if score >= 2:
        return "agresivo"

    return "moderado"


def registrar_usuario(
    *,
    username: str,
    password: str,
    full_name: str,
    age: int,
    experience: int,
    tolerance: int,
    investment_objective: str,
    recovery_code: str,
    accepted_habeas_data: bool,
) -> tuple[bool, str]:
    username = str(username or "").strip().lower()
    password = str(password or "")
    full_name = str(full_name or "").strip()
    recovery_code = _normalise_recovery_code(recovery_code)

    if len(username) < 4:
        return False, "El usuario debe tener mínimo 4 caracteres."

    if len(password) < 6:
        return False, "La contraseña debe tener mínimo 6 caracteres."

    if not full_name:
        return False, "Debes ingresar tu nombre completo."

    if not accepted_habeas_data:
        return False, "Debes aceptar el tratamiento de datos personales para crear la cuenta."

    code_error = _recovery_code_error(recovery_code)
    if code_error:
        return False, code_error

    if _username_exists_for_registration(username):
        return False, "Ese usuario ya existe. Prueba con otro nombre de usuario."

    fallback_profile = _risk_profile_from_registration(
        age=int(age),
        experience=int(experience),
        tolerance=int(tolerance),
        objective=investment_objective,
    )

    users = _load_users_for_registration()

    users.append(
        {
            "username": username,
            "role": "user",
            "password": password,
            "full_name": full_name,
            "kyc": {
                "age": int(age),
                "experience": int(experience),
                "tolerance": int(tolerance),
                "investment_objective": investment_objective,
                "preferred_horizon": None,
                "fallback_profile": fallback_profile,
            },
            "recovery_code": recovery_code,
            "accepted_habeas_data": True,
        }
    )

    _save_users_for_registration(users)

    return True, "Usuario registrado correctamente."

def verificar_login(username, password):
    username = str(username or "").strip().lower()

    try:
        with open("backend/data/users.json", "r", encoding="utf-8-sig") as f:
            db = json.load(f)

        for u in db.get("users", []):
            current_username = str(u.get("username", "")).strip().lower()

            if current_username == username and u.get("password") == password:
                user_kyc = u.get("kyc", {}) or {}

                st.session_state.logged_in = True
                st.session_state.user_role = u.get("role", "user")
                st.session_state.user_name = u.get("full_name", username)
                st.session_state.user_username = u.get("username", username)
                st.session_state.user_kyc_data = user_kyc
                st.session_state.user_preferred_horizon = user_kyc.get("preferred_horizon")
                st.session_state.kyc_profile = user_kyc.get("fallback_profile")
                st.session_state.user_has_recovery_code = bool(str(u.get("recovery_code", "")).strip())
                return True

    except FileNotFoundError:
        st.error("Base de datos de usuarios no encontrada.")

    return False

def _logout() -> None:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.user_username = None
    st.session_state.user_has_recovery_code = True
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
            width: min(80vw, 1560px);
            max-width: min(80vw, 1560px);
            padding-top: 1.1rem;
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-left: auto;
            margin-right: auto;
        }

        div[data-testid="stForm"] {
            background: rgba(8, 24, 58, 0.68) !important;
            border: 1px solid rgba(180, 218, 255, 0.18) !important;
            border-radius: 22px !important;
            padding: 1.65rem !important;
            box-shadow: 0 24px 55px rgba(0, 0, 0, 0.26) !important;
            backdrop-filter: blur(18px);
        }

        div[data-testid="stForm"] label,
        div[data-testid="stForm"] p {
            color: #D8E6FF !important;
            font-size: 0.95rem !important;
            font-weight: 850 !important;
        }

        div[data-testid="stForm"] input,
        div[data-testid="stForm"] [data-baseweb="input"] input,
        div[data-testid="stForm"] [data-baseweb="base-input"] input {
            background: #FFFFFF !important;
            border: 1px solid rgba(180, 218, 255, 0.36) !important;
            border-radius: 12px !important;
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
            caret-color: #0F172A !important;
            opacity: 1 !important;
            min-height: 44px !important;
            font-size: 0.98rem !important;
        }

        div[data-testid="stForm"] input::placeholder {
            color: #64748B !important;
            -webkit-text-fill-color: #64748B !important;
            opacity: 1 !important;
        }

        div[data-testid="stExpander"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, #FFF7FA 100%) !important;
            border: 1px solid rgba(138, 21, 56, 0.44) !important;
            border-radius: 18px !important;
            box-shadow: 0 16px 38px rgba(138, 21, 56, 0.22) !important;
            overflow: hidden !important;
        }

        div[data-testid="stExpander"] details,
        div[data-testid="stExpander"] summary {
            background: transparent !important;
        }

        div[data-testid="stExpander"] summary {
            border-left: 7px solid #8A1538 !important;
            min-height: 68px !important;
            padding: 0.9rem 1rem !important;
            background:
                linear-gradient(90deg, rgba(138, 21, 56, 0.13) 0%, rgba(255, 255, 255, 0.98) 52%, rgba(37, 99, 235, 0.08) 100%) !important;
        }

        div[data-testid="stExpander"] summary *,
        div[data-testid="stExpander"] summary p,
        div[data-testid="stExpander"] summary span,
        div[data-testid="stExpander"] summary svg {
            color: #8A1538 !important;
            -webkit-text-fill-color: #8A1538 !important;
            stroke: #8A1538 !important;
            opacity: 1 !important;
            font-weight: 950 !important;
            font-size: 1.02rem !important;
            letter-spacing: 0 !important;
        }

        div[data-testid="stExpander"] details > div,
        div[data-testid="stExpander"] details > div * {
            background: #FFFFFF !important;
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
            opacity: 1 !important;
        }

        div[data-testid="stExpander"] label p {
            color: #0F2A4D !important;
            -webkit-text-fill-color: #0F2A4D !important;
            font-weight: 950 !important;
        }

        div[data-testid="stCheckbox"] label {
            background: #F8FBFF !important;
            border: 1px solid rgba(37, 99, 235, 0.22) !important;
            border-radius: 14px !important;
            padding: 0.7rem 0.85rem !important;
            width: 100% !important;
        }

        div[data-testid="stCheckbox"] label p {
            color: #0F2A4D !important;
            -webkit-text-fill-color: #0F2A4D !important;
            font-weight: 900 !important;
        }

        div[data-testid="stCheckbox"] svg {
            color: #0B6B38 !important;
            fill: #0B6B38 !important;
            stroke: #0B6B38 !important;
        }

        .terms-accepted-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            margin: 0.15rem 0 0.85rem 0;
            padding: 0.58rem 0.78rem;
            border-radius: 999px;
            border: 1px solid rgba(11, 107, 56, 0.28);
            background: linear-gradient(180deg, #E8FFF2 0%, #D7FBE8 100%);
            color: #064E2B !important;
            -webkit-text-fill-color: #064E2B !important;
            font-size: 0.86rem;
            font-weight: 950;
            box-shadow: 0 10px 24px rgba(11, 107, 56, 0.14);
        }

        .login-card-header {
            background: rgba(8, 24, 58, 0.68);
            border: 1px solid rgba(180, 218, 255, 0.18);
            border-radius: 22px;
            padding: 1.65rem 1.65rem 1.35rem 1.65rem;
            margin-bottom: 1rem;
            min-height: 128px;
            box-shadow: 0 18px 44px rgba(0, 0, 0, 0.20);
            backdrop-filter: blur(18px);
        }

        .login-card-title {
            font-size: 1.72rem !important;
            line-height: 1.08 !important;
        }

        .login-card-subtitle {
            font-size: 1rem !important;
            margin-top: 0.45rem !important;
        }

        [data-testid="stFormSubmitButton"] button {
            min-height: 52px !important;
            font-size: 1rem !important;
            font-weight: 950 !important;
        }

        @media (max-width: 1100px) {
            .block-container {
                width: 94vw;
                max-width: 94vw;
            }
        }
    </style>
    """


def _logo_html() -> str:
    logo_b64 = image_to_base64(LOGO_PATH)
    if not logo_b64:
        return '<div class="login-logo"></div>'
    return f'<img class="login-logo" src="data:image/png;base64,{logo_b64}" alt="P.R.ED">'


def _render_login() -> None:
    st.set_page_config(
        page_title="Acceso | P.R.ED",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(build_global_css("General"), unsafe_allow_html=True)
    st.markdown(_login_css(), unsafe_allow_html=True)

    left, right = st.columns([1.16, 0.84], gap="large")

    with left:
        st.markdown(
            f"""
            <div class="login-stage">
                <div class="login-glow one"></div>
                <div class="login-glow two"></div>
                <div class="login-brand" style="position:relative;z-index:1;">
                    {_logo_html()}
                    <div>
                        <div class="login-brand-title">P.R.ED</div>
                        <div class="login-brand-subtitle">Generador de Portafolios de riesgo</div>
                    </div>
                </div>
                <div class="login-title" style="position:relative;z-index:1;margin:6.6rem auto 0 auto;text-align:center;">Welcome back...</div>
                <div class="login-subtitle" style="position:relative;z-index:1;margin-left:auto;margin-right:auto;text-align:center;">
                    Riesgo, valoración, optimización y automatización Perri en un entorno financiero profesional.
                </div>
                <div class="login-trust-row" style="position:relative;z-index:1;justify-content:center;">
                    <span class="login-trust">FastAPI</span>
                    <span class="login-trust">Streamlit</span>
                    <span class="login-trust">SQLite</span>
                    <span class="login-trust">Perri</span>
                </div>
                <div class="login-quote-card">
                    <div class="login-quote-mark">Lectura P.R.ED</div>
                    <div class="login-quote-text">
                        “We simply attempt to be fearful when others are greedy and to be greedy only when others are fearful”.
                    </div>
                    <div class="login-quote-source">
                        Buffett, W. E. (16 de octubre de 2008). <em>Buy American. I am.</em>
                        The New York Times.
                        <a href="https://www.nytimes.com/2008/10/17/opinion/17buffett.html" target="_blank" rel="noopener noreferrer">
                            nytimes.com
                        </a>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="login-card-header">
                <div class="login-card-title">Iniciar sesión</div>
                <div class="login-card-subtitle">Ingresa con tus credenciales asignadas.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input(
                "Usuario",
                value=st.session_state.get("login_prefill_username", ""),
                placeholder="Usuario",
            )
            password = st.text_input("Contraseña", type="password", placeholder="Contraseña")
            submitted = st.form_submit_button("Ingresar", use_container_width=True)

            if submitted:
                if verificar_login(username.strip(), password):
                    st.success(f"Bienvenido, {st.session_state.user_name}.")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

        register_message = st.session_state.pop("register_success_message", "")
        if register_message:
            st.success(register_message)

        reset_message = st.session_state.pop("reset_success_message", "")
        if reset_message:
            st.success(reset_message)

        with st.expander("¿Olvidaste tu contraseña? · Cambiar contraseña", expanded=False):
            st.caption("Usa la clave de recuperación que guardaste al crear tu cuenta.")

            with st.container():
                reset_username = st.text_input("**Usuario registrado**", placeholder="Usuario")
                reset_code = st.text_input(
                    "**Clave de recuperación**",
                    placeholder="Ej: 20/FEB/2003",
                    key="reset_recovery_code",
                    help=(
                        "Debe ser la misma secuencia que escribiste cuando creaste la cuenta. "
                        "Se convierte automáticamente a mayúsculas y no conserva espacios."
                    ),
                    on_change=_normalise_recovery_code_state,
                    args=("reset_recovery_code",),
                )
                reset_new_password = st.text_input("**Nueva contraseña**", type="password", placeholder="Mínimo 6 caracteres")
                reset_confirm_password = st.text_input("**Confirmar nueva contraseña**", type="password")
                reset_submitted = st.button("Actualizar contraseña", use_container_width=True, key="reset_password_submit")

                if reset_submitted:
                    if reset_new_password != reset_confirm_password:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        ok, message = actualizar_password_por_recuperacion(
                            username=reset_username,
                            recovery_code=reset_code,
                            new_password=reset_new_password,
                        )

                        if not ok:
                            st.error(message)
                        else:
                            st.session_state.login_prefill_username = str(reset_username or "").strip().lower()
                            st.session_state.reset_success_message = message
                            st.rerun()

        with st.expander("¿No tienes cuenta? · Crear cuenta nueva", expanded=st.session_state.get("show_register_panel", False)):
            st.caption("Registra tus datos personales para estimar tu perfil de riesgo inicial.")

            with st.container():
                full_name = st.text_input("**Nombre completo**", placeholder="Ej: Juan Pérez")
                new_username = st.text_input("**Usuario nuevo**", placeholder="Mínimo 4 caracteres")
                new_password = st.text_input("**Contraseña nueva**", type="password", placeholder="Mínimo 6 caracteres")
                confirm_password = st.text_input("**Confirmar contraseña**", type="password")
                recovery_code = st.text_input(
                    "**Clave de recuperación**",
                    placeholder="Ej: 20/FEB/2003",
                    key="register_recovery_code",
                    help=(
                        "Escribe una secuencia fácil de recordar, con letras y números. "
                        "Servirá para cambiar tu contraseña si la olvidas. "
                        "Se convierte automáticamente a mayúsculas y no conserva espacios."
                    ),
                    on_change=_normalise_recovery_code_state,
                    args=("register_recovery_code",),
                )

                col_reg_1, col_reg_2 = st.columns(2)

                with col_reg_1:
                    age = st.number_input("**Edad**", min_value=18, max_value=150, value=30, step=1)
                    experience = st.number_input("**Experiencia invirtiendo (años)**", min_value=0, max_value=100, value=1, step=1)

                with col_reg_2:
                    tolerance = st.selectbox(
                        "**Tolerancia al riesgo**",
                        options=[1, 2, 3, 4, 5],
                        index=2,
                        format_func=lambda value: {
                            1: "1 - Conservadora",
                            2: "2 - Baja",
                            3: "3 - Moderada",
                            4: "4 - Alta",
                            5: "5 - Agresiva",
                        }[value],
                        help="Escala de 1 a 5: 1 es conservadora y 5 es agresiva.",
                    )
                    investment_objective = st.selectbox(
                        "**Objetivo principal**",
                        options=[
                            "preservacion_capital",
                            "crecimiento_controlado",
                            "crecimiento",
                        ],
                        format_func=lambda value: {
                            "preservacion_capital": "Preservación de capital",
                            "crecimiento_controlado": "Crecimiento controlado",
                            "crecimiento": "Crecimiento agresivo",
                        }.get(value, value),
                        index=1,
                    )

                st.markdown(
                    """
                    **Ref. Autorización para el tratamiento y uso de datos personales.**

                    De conformidad con lo previsto en la Ley 1581 de 2012, por la cual se dictan
                    las disposiciones generales para la protección de datos personales, y el
                    Decreto 1377 de 2013, que la reglamenta parcialmente, manifiesto que otorgo
                    mi autorización expresa y clara para que PRED pueda hacer tratamiento y uso
                    de mis datos personales, los cuales estarán reportados en la base de datos
                    de la que es responsable esta organización y que han sido recolectados en el
                    marco del uso académico del presente dashboard.

                    De acuerdo con la normatividad citada, PRED queda autorizado de manera
                    expresa e inequívoca para mantener y manejar la información suministrada,
                    solo para finalidades académicas relacionadas con el análisis de riesgo,
                    estimación de perfil del inversionista, simulación financiera, generación
                    de reportes y evaluación del funcionamiento del sistema, respetando en todo
                    caso la normatividad vigente sobre protección de datos personales.

                    No obstante la presente autorización, me reservo el derecho a ejercer en
                    cualquier momento la posibilidad de conocer, actualizar, rectificar y
                    solicitar la supresión de mis datos personales en la base de datos de PRED,
                    cuando así lo estime conveniente.
                    """
                )
                accepted_habeas_data = st.checkbox("He leído y acepto la autorización de tratamiento y uso de datos personales.")

                if accepted_habeas_data:
                    st.markdown('<div class="terms-accepted-pill">✓ Términos aceptados</div>', unsafe_allow_html=True)

                register_submitted = st.button("Crear cuenta", use_container_width=True, type="primary")

                if register_submitted:
                    if new_password != confirm_password:
                        st.session_state.show_register_panel = True
                        st.error("Las contraseñas no coinciden.")
                    else:
                        ok, message = registrar_usuario(
                            username=new_username,
                            password=new_password,
                            full_name=full_name,
                            age=int(age),
                            experience=int(experience),
                            tolerance=int(tolerance),
                            investment_objective=investment_objective,
                            recovery_code=recovery_code,
                            accepted_habeas_data=bool(accepted_habeas_data),
                        )

                        if not ok:
                            st.session_state.show_register_panel = True
                            st.error(message)
                        else:
                            st.session_state.show_register_panel = False
                            st.session_state.login_prefill_username = str(new_username or "").strip().lower()
                            st.session_state.register_success_message = (
                                "Cuenta creada correctamente. Ya puedes ingresar con ese usuario y contraseña."
                            )
                            st.rerun()
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
    groups = dict(MODULE_GROUPS)
    if st.session_state.get("user_role") == "superuser":
        groups["Administración"] = [
            ("Admin", "Usuarios", "Consulta, descarga y eliminación de usuarios registrados.", "pages/15_Usuarios.py")
        ]

    group_tabs = st.tabs(list(groups.keys()))

    for tab, (_, modules) in zip(group_tabs, groups.items()):
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


def _render_missing_recovery_code_prompt() -> None:
    if st.session_state.get("user_has_recovery_code", True):
        return

    with st.expander("Tu cuenta no tiene clave de recuperación · Configurar ahora", expanded=False):
        st.caption(
            "Esta clave te servirá para cambiar tu contraseña si la olvidas. Usa una secuencia con letras y números, por ejemplo 20/FEB/2003."
        )
        with st.container():
            recovery_code = st.text_input(
                "**Nueva clave de recuperación**",
                placeholder="Ej: 20/FEB/2003",
                key="setup_recovery_code",
                on_change=_normalise_recovery_code_state,
                args=("setup_recovery_code",),
            )
            recovery_code_confirm = st.text_input(
                "**Confirmar clave de recuperación**",
                placeholder="Repite la clave",
                key="setup_recovery_code_confirm",
                on_change=_normalise_recovery_code_state,
                args=("setup_recovery_code_confirm",),
            )
            submitted = st.button("Guardar clave de recuperación", use_container_width=True, key="setup_recovery_code_submit")

            if submitted:
                if _normalise_recovery_code(recovery_code) != _normalise_recovery_code(recovery_code_confirm):
                    st.error("Las claves de recuperación no coinciden.")
                else:
                    ok, message = actualizar_clave_recuperacion_usuario(
                        st.session_state.get("user_username", ""),
                        recovery_code,
                    )
                    if ok:
                        st.session_state.user_has_recovery_code = True
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)


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
        title="P.R.ED",
        subtitle="Desarrolla Tus Portafolios",
        filtros_label="Parámetros generales",
        filtros_expanded=False,
        page_title="P.R.ED",
        page_icon="📊",
    )

    with filtros_panel:
        st.caption("Panel de inicio")
        st.write("Usa las pestañas superiores para navegar por módulos y este panel para opciones generales.")

    _render_missing_recovery_code_prompt()

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


    seccion("Configuración inicial global del portafolio")
    render_global_portfolio_config()


_init_session_state()

if not st.session_state.logged_in:
    _render_login()

_render_home()

