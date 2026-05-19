from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_ui import (
    header_dashboard,
    nota,
    plot_card_footer,
    plot_card_header,
    seccion,
    tarjeta_kpi,
)
from ui.page_setup import setup_dashboard_page
from ui.plot_style import style_plotly_figure


def _format_number(value: float) -> str:
    return f"{float(value):,.4f}"


setup_dashboard_page(
    page_title="Opciones",
    page_icon="📈",
)

header_dashboard(
    title="Módulo 10 — Opciones",
    subtitle="Valoración de opciones europeas con Black-Scholes y cinco Greeks.",
)

client = get_api_client()

seccion("Parámetros de valoración")

with st.sidebar:
    st.markdown("### Black-Scholes")

    option_type = st.selectbox("Tipo de opción", ["call", "put"])
    spot_price = st.number_input("Spot S", min_value=0.01, value=100.0, step=1.0)
    strike_price = st.number_input("Strike K", min_value=0.01, value=105.0, step=1.0)
    time_to_maturity = st.number_input("Tiempo T en años", min_value=0.01, value=1.0, step=0.25)
    risk_free_rate = st.number_input("Tasa libre de riesgo r", value=0.05, step=0.01, format="%.4f")
    volatility = st.number_input("Volatilidad sigma", min_value=0.0001, value=0.20, step=0.01, format="%.4f")

payload = {
    "spot_price": float(spot_price),
    "strike_price": float(strike_price),
    "time_to_maturity": float(time_to_maturity),
    "risk_free_rate": float(risk_free_rate),
    "volatility": float(volatility),
    "option_type": option_type,
}

render_info_card(
    "Black-Scholes",
    "Este módulo valora una opción europea y calcula delta, gamma, vega, theta y rho.",
)

if st.button("Calcular opción", type="primary"):
    try:
        result = client.post("/valuation/black-scholes", json_payload=payload, include_api_key=True)

        greeks = result["greeks"]

        seccion("Resultado de valoración")

        col1, col2, col3 = st.columns(3)
        with col1:
            tarjeta_kpi("Precio teórico", _format_number(result["price"]))
        with col2:
            tarjeta_kpi("Delta", _format_number(greeks["delta"]))
        with col3:
            tarjeta_kpi("Gamma", _format_number(greeks["gamma"]))

        col4, col5, col6 = st.columns(3)
        with col4:
            tarjeta_kpi("Vega", _format_number(greeks["vega"]))
        with col5:
            tarjeta_kpi("Theta", _format_number(greeks["theta"]))
        with col6:
            tarjeta_kpi("Rho", _format_number(greeks["rho"]))

        render_meta_row(
            {
                "Tipo": option_type.upper(),
                "Spot": _format_number(spot_price),
                "Strike": _format_number(strike_price),
                "Volatilidad": f"{volatility:.2%}",
            }
        )

        seccion("Payoff a vencimiento")

        spot_range = np.linspace(max(0.01, spot_price * 0.5), spot_price * 1.5, 80)

        if option_type == "call":
            payoff = np.maximum(spot_range - strike_price, 0)
        else:
            payoff = np.maximum(strike_price - spot_range, 0)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=spot_range,
                y=payoff,
                mode="lines",
                name=f"Payoff {option_type}",
            )
        )
        fig.add_vline(x=strike_price, line_dash="dash", annotation_text="Strike")

        fig.update_layout(
            title="Payoff a vencimiento",
            xaxis_title="Precio del subyacente al vencimiento",
            yaxis_title="Payoff",
        )

        plot_card_header("Curva de payoff")
        st.plotly_chart(style_plotly_figure(fig), use_container_width=True)
        plot_card_footer("El payoff muestra el valor intrínseco de la opción al vencimiento.")

        nota(
            "La valoración usa Black-Scholes para precio teórico y sensibilidad mediante las cinco Greeks exigidas por la rúbrica."
        )

    except ApiClientError as exc:
        st.error(f"Error al consumir backend de opciones: {exc.message}")
    except Exception as exc:
        st.error(f"Error inesperado: {exc}")
else:
    nota("Ajusta los parámetros en la barra lateral y calcula la opción.")
