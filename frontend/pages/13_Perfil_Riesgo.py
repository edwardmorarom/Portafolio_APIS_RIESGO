from __future__ import annotations

import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_ui import header_dashboard, nota, seccion, tarjeta_kpi
from ui.page_setup import setup_dashboard_page


modo, filtros_panel = setup_dashboard_page(
    title="Perfil de riesgo",
    subtitle="Universidad Santo Tomás",
    filtros_label="Parámetros KYC",
    filtros_expanded=True,
    page_title="Perfil de Riesgo",
    page_icon="🧾",
)

client = get_api_client()

with filtros_panel:
    age = st.number_input("Edad", min_value=18, max_value=100, value=30, step=1)
    experience = st.number_input("Años de experiencia invirtiendo", min_value=0, max_value=60, value=2, step=1)
    tolerance = st.slider("Tolerancia al riesgo", min_value=1, max_value=5, value=3)

header_dashboard(
    "Perfil de riesgo KYC",
    "Calcula un perfil sugerido para conectar al inversionista con RoboAdvisor, Markowitz y lectura financiera.",
    modo=modo,
)

nota(
    "Este módulo usa edad, experiencia y tolerancia al riesgo para sugerir un perfil conservador, moderado o agresivo."
)

payload = {
    "age": int(age),
    "experience": int(experience),
    "tolerance": int(tolerance),
}

result = None

if st.button("Calcular perfil sugerido", type="primary", use_container_width=True):
    try:
        result = client.suggest_kyc_profile(payload)
        st.session_state["kyc_profile"] = result.get("suggested_profile")
        st.session_state["kyc_score"] = result.get("score")
        st.session_state["kyc_explanation"] = result.get("explanation")
        st.success("Perfil KYC calculado y guardado en la sesión.")
    except ApiClientError as exc:
        st.error(f"Error al consultar KYC: {exc.message}")
    except Exception as exc:
        st.error(f"Error inesperado: {exc}")

profile = st.session_state.get("kyc_profile")
score = st.session_state.get("kyc_score")
explanation = st.session_state.get("kyc_explanation")

seccion("Resultado KYC")

if profile:
    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta_kpi("Perfil sugerido", str(profile).upper(), subtexto="Resultado del motor KYC")
    with c2:
        tarjeta_kpi("Score", str(score), subtexto="Puntaje total")
    with c3:
        tarjeta_kpi("Tolerancia", str(tolerance), subtexto="Escala 1 a 5")

    render_meta_row(
        {
            "Edad": age,
            "Experiencia": f"{experience} años",
            "Perfil": profile,
        }
    )

    render_info_card("Interpretación", explanation or "Perfil calculado correctamente.")
else:
    render_info_card("Pendiente", "Ejecuta el cálculo para obtener el perfil sugerido.")
