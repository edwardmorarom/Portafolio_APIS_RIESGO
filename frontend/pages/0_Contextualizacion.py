from __future__ import annotations

import streamlit as st

from config import COMPANY_LOGOS
from services.api_client import get_assets
from ui.page_setup import setup_dashboard_page
from ui.dashboard_ui import header_dashboard, nota, seccion


ASSET_DESCRIPTIONS = {
    "BP.L": {
        "desc": "Multinacional energética con exposición a petróleo, gas y transición energética.",
        "role": "Aporta sensibilidad macro y exposición al ciclo energético global.",
    },
    "CA.PA": {
        "desc": "Retail defensivo europeo con foco en consumo masivo y operación internacional.",
        "role": "Funciona como componente estable ligado al consumo básico.",
    },
    "ATD.TO": {
        "desc": "Operador global de tiendas de conveniencia y estaciones de servicio.",
        "role": "Aporta diversificación operativa, geográfica y exposición a retail internacional.",
    },
    "FEMSAUBD.MX": {
        "desc": "Conglomerado mexicano con negocios en retail, bebidas y logística.",
        "role": "Introduce exposición regional a Latinoamérica y diversificación corporativa.",
    },
    "3382.T": {
        "desc": "Grupo japonés de retail con presencia internacional y reconocimiento de marca.",
        "role": "Añade exposición asiática y diversificación por región y estructura operativa.",
    },
}


modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros Del Módulo",
    filtros_expanded=True,
)

with filtros_sidebar:
    st.caption("Este módulo presenta la lógica general del portafolio y la identidad de los activos base.")


header_dashboard(
    "Contextualización del portafolio",
    "Comprende la lógica estratégica de los activos seleccionados y su papel dentro del análisis.",
    modo=modo,
)

if modo == "General":
    nota("Esta sección presenta los activos base del proyecto y el sentido general del portafolio.")
else:
    nota("Esta sección sirve como marco interpretativo para los módulos cuantitativos posteriores.")


seccion("Resumen general")

c1, c2, c3 = st.columns(3)

with c1:
    with st.container(border=True):
        st.markdown("###### NÚMERO DE ACTIVOS BASE")
        st.markdown("## 5")
        st.write("BP, Carrefour, Couche-Tard, FEMSA y Seven & i.")

with c2:
    with st.container(border=True):
        st.markdown("###### COBERTURA GEOGRÁFICA")
        st.markdown("## Global")
        st.write("Europa, América y Asia.")

with c3:
    with st.container(border=True):
        st.markdown("###### LÓGICA DEL PORTAFOLIO")
        st.markdown("## Diversificación")
        st.write("Combina retail defensivo, consumo y energía.")


seccion("Empresas del portafolio")

try:
    assets_data = get_assets()
    assets = assets_data.get("assets", [])
except Exception as exc:
    st.error(f"No se pudo cargar el universo de activos desde el backend: {exc}")
    assets = []

default_assets = [a for a in assets if a.get("default") is True]

if not default_assets:
    st.warning("No se encontraron activos predeterminados en el backend.")
else:
    cols = st.columns(2)

    for i, asset in enumerate(default_assets):
        with cols[i % 2]:
            ticker = asset.get("ticker", "")
            extra = ASSET_DESCRIPTIONS.get(ticker, {})
            desc = extra.get("desc", "Activo incluido dentro del universo base del portafolio.")
            role = extra.get("role", "Cumple un rol de diversificación dentro del portafolio.")

            with st.container(border=True):
                logo_col, info_col = st.columns([1, 2])

                with logo_col:
                    logo_path = COMPANY_LOGOS.get(ticker)
                    if logo_path:
                        try:
                            st.image(logo_path, width=115)
                        except Exception:
                            pass

                with info_col:
                    st.markdown("###### ACTIVO")
                    st.markdown(f"### {asset.get('name', 'Activo')}")
                    st.write(desc)
                    st.write(f"**Ticker:** {ticker}")
                    st.write(f"**País:** {asset.get('country', 'N/D')}")
                    st.write(f"**Predeterminado:** {'Sí' if asset.get('default') else 'No'}")

                st.info(f"**Rol en el portafolio:** {role}")


seccion("Lectura del módulo")

nota(
    "Este portafolio fue planteado para analizar diversificación internacional, riesgo de mercado, "
    "sensibilidad frente al benchmark, riesgo extremo, volatilidad condicional y decisiones integradas "
    "de inversión bajo distintos enfoques estadísticos y financieros."
)