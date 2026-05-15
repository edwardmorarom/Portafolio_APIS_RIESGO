import streamlit as st
import json
from ui.page_setup import setup_dashboard_page
from ui.dashboard_ui import header_dashboard, nota

# --- LÓGICA DE LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_name = None

def verificar_login(username, password):
    try:
        with open("backend/data/users.json", "r", encoding="utf-8-sig") as f:
            db = json.load(f)
            for u in db["users"]:
                if u["username"] == username and u["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_role = u["role"]
                    st.session_state.user_name = u["full_name"]
                    return True
    except FileNotFoundError:
        st.error("Base de datos de usuarios no encontrada.")
    return False

# Pantalla de bloqueo si no está logueado
if not st.session_state.logged_in:
    # 1. Colapsar el sidebar por defecto
    st.set_page_config(page_title="Login - RoboAdvisor USTA", page_icon="🔐", layout="centered", initial_sidebar_state="collapsed")
    
    # 2. Inyección CSS para desaparecer el menú de navegación y el botón de expandir
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {display: none;}
            [data-testid="collapsedControl"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    st.title("🔐 Acceso al Robo-Advisor Institucional")
    st.markdown("Por favor, inicie sesión para continuar.")
    
    with st.form("login_form"):
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Ingresar")
        
        if submit:
            if verificar_login(user, pwd):
                st.success(f"Bienvenido, {st.session_state.user_name}!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    st.stop() 

# --- APP PRINCIPAL ---
modo, _ = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    filtros_label="Parámetros Generales",
)

header_dashboard(
    "Dashboard de Riesgo de Portafolio",
    "Proyecto integrador de Teoría del Riesgo y APIs",
    modo=modo,
)

st.write(f"👤 Usuario activo: **{st.session_state.user_name}** | Rol: **{st.session_state.user_role.upper()}**")

if st.session_state.user_role == "superuser":
    st.info("👑 Modo Super-Usuario: Tienes acceso a la gestión de la Reserva de Activos y auditoría de KYC.")
    if st.button("Cerrar Sesión", key="logout_btn"):
        st.session_state.logged_in = False
        st.rerun()

if modo == "General":
    nota("Usa el menú lateral para navegar entre módulos del dashboard.")
else:
    nota("Modo estadístico activo. La interfaz prioriza lectura técnica e interpretación cuantitativa.")