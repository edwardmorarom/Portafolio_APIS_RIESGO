from __future__ import annotations

import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_filters import render_filter_help
from ui.dashboard_ui import header_dashboard, nota, seccion, tarjeta_kpi
from ui.page_setup import setup_dashboard_page
from ui.portfolio_state import active_config, render_portfolio_scope_note


modo, filtros_panel = setup_dashboard_page(
    title="Perfil de riesgo",
    subtitle="Universidad Santo Tomas",
    filtros_label="Parametros KYC",
    filtros_expanded=True,
    page_title="Perfil de Riesgo",
    page_icon="KYC",
)

client = get_api_client()
config = active_config()
stored_profile = config.get("risk_profile") or st.session_state.get("kyc_profile")
stored_kyc = config.get("kyc", {}) or st.session_state.get("user_kyc_data", {}) or {}

with filtros_panel:
    render_portfolio_scope_note()
    render_filter_help(
        "Como llenar KYC",
        "Edad, experiencia y tolerancia permiten aproximar el perfil del inversionista. El resultado se usa para sustentar decisiones de riesgo y recomendacion.",
    )
    age = st.number_input("Edad", min_value=18, max_value=100, value=int(stored_kyc.get("age", 30)), step=1, help="Edad del inversionista. Ayuda a aproximar horizonte y tolerancia.")
    experience = st.number_input("Años de experiencia invirtiendo", min_value=0, max_value=60, value=int(stored_kyc.get("experience", 2)), step=1, help="Experiencia financiera acumulada del usuario, medida en años.")
    stored_tolerance = max(1, min(5, int(stored_kyc.get("tolerance", 3))))
    tolerance = st.selectbox(
        "Tolerancia al riesgo",
        options=[1, 2, 3, 4, 5],
        index=stored_tolerance - 1,
        format_func=lambda value: {
            1: "1 - Conservadora",
            2: "2 - Baja",
            3: "3 - Moderada",
            4: "4 - Alta",
            5: "5 - Agresiva",
        }[value],
        help="Escala de 1 a 5: 1 es conservador y 5 es agresivo.",
    )

header_dashboard(
    "Perfil de riesgo KYC",
    "Calcula un perfil sugerido para conectar al inversionista con RoboAdvisor, Markowitz y lectura financiera.",
    modo=modo,
)

nota(
    "Este modulo usa edad, experiencia y tolerancia al riesgo para sugerir un perfil conservador, moderado o agresivo."
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
        st.success("Perfil KYC calculado y guardado en la sesion.")
    except ApiClientError as exc:
        st.error(f"Error al consultar KYC: {exc.message}")
    except Exception as exc:
        st.error(f"Error inesperado: {exc}")

profile = st.session_state.get("kyc_profile") or stored_profile
score = st.session_state.get("kyc_score")
explanation = st.session_state.get("kyc_explanation")

seccion("Resultado KYC")

if profile:
    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta_kpi("Perfil sugerido", str(profile).upper(), subtexto="Resultado del motor KYC", help_text="Perfil estimado a partir de edad, experiencia y tolerancia.")
    with c2:
        tarjeta_kpi("Score", str(score), subtexto="Puntaje total", help_text="Puntaje usado por el motor KYC para ubicar el perfil.")
    with c3:
        tarjeta_kpi("Tolerancia", str(tolerance), subtexto="Escala 1 a 5", help_text="Nivel declarado de disposicion a asumir riesgo.")

    render_meta_row(
        {
            "Edad": age,
            "Experiencia": f"{experience} años",
            "Perfil": profile,
        }
    )

    render_info_card("Interpretacion", explanation or "Perfil calculado correctamente.")
    report_payload = {
        "portfolio_context": {
            "profile": profile,
            "score": score,
            "age": int(age),
            "experience": int(experience),
            "tolerance": int(tolerance),
            "tickers": config.get("tickers", []),
            "weights_pct": config.get("weights_pct", []),
            "horizon": config.get("horizon_type"),
            "benchmark": config.get("benchmark", {}),
        },
        "key_results": {
            "perfil_riesgo": profile,
            "score_kyc": score,
            "tolerancia": tolerance,
        },
        "sections": [
            {
                "title": "Perfil de riesgo",
                "content": explanation or "Perfil calculado con el motor KYC del proyecto.",
            },
            {
                "title": "Uso en el dashboard",
                "content": "El perfil se conserva para sustentar decisiones de portafolio, riesgo, Markowitz, RoboAdvisor y reporte final.",
            },
        ],
    }
    try:
        pdf_bytes = client.build_executive_summary_pdf(report_payload)
        st.download_button(
            "Descargar perfil de riesgo en PDF",
            data=pdf_bytes,
            file_name="perfil_riesgo.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except ApiClientError as exc:
        st.warning(f"No fue posible generar el PDF: {exc.message}")
    except Exception as exc:
        st.warning(f"No fue posible generar el PDF: {exc}")
else:
    render_info_card("Pendiente", "Ejecuta el calculo para obtener el perfil sugerido o conserva el perfil elegido en Inicio.")
