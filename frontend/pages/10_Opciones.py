from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_ui import header_dashboard, nota, plot_card_footer, plot_card_header, seccion, tarjeta_kpi
from ui.page_setup import setup_dashboard_page
from ui.plot_style import style_plotly_figure
from ui.portfolio_state import render_portfolio_scope_note


def _format_num(value: float) -> str:
    return f"{float(value):,.4f}"


def _format_money(value: float) -> str:
    return f"${float(value):,.2f}"


modo, filtros_panel = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    filtros_label="Parámetros de opciones",
    filtros_expanded=True,
    page_title="Opciones",
    page_icon="📈",
)

client = get_api_client()

with filtros_panel:
    render_portfolio_scope_note()
    option_type = st.selectbox("Tipo de opción", ["call", "put"])
    spot_price = st.number_input("Spot S", min_value=0.01, value=100.0, step=1.0)
    strike_price = st.number_input("Strike K", min_value=0.01, value=105.0, step=1.0)
    time_to_maturity = st.number_input("Tiempo T en años", min_value=0.01, value=1.0, step=0.25)
    risk_free_rate = st.number_input("Tasa libre de riesgo r", value=0.05, step=0.01, format="%.4f")
    volatility = st.number_input("Volatilidad sigma", min_value=0.0001, value=0.20, step=0.01, format="%.4f")
    run_analysis = st.button("Calcular opción", type="primary", use_container_width=True)

payload = {
    "spot_price": float(spot_price),
    "strike_price": float(strike_price),
    "time_to_maturity": float(time_to_maturity),
    "risk_free_rate": float(risk_free_rate),
    "volatility": float(volatility),
    "option_type": option_type,
}

header_dashboard(
    "Opciones",
    "Valoración Black-Scholes, Greeks y sensibilidad de una opción europea.",
    modo=modo,
)

tab_value, tab_payoff, tab_sensitivity = st.tabs(["Valoración", "Payoff", "Sensibilidad"])

result: dict | None = None
sensitivity_rows: list[dict] = []

if run_analysis:
    try:
        result = client.post("/valuation/black-scholes", json_payload=payload, include_api_key=True)

        for vol in np.linspace(max(0.01, volatility * 0.5), volatility * 1.8, 8):
            scenario = dict(payload)
            scenario["volatility"] = float(vol)
            scenario_result = client.post("/valuation/black-scholes", json_payload=scenario, include_api_key=True)
            sensitivity_rows.append(
                {
                    "Volatilidad": float(vol),
                    "Precio": float(scenario_result["price"]),
                    "Delta": float(scenario_result["greeks"]["delta"]),
                    "Vega": float(scenario_result["greeks"]["vega"]),
                }
            )
    except ApiClientError as exc:
        st.error(f"Error al consumir backend de opciones: {exc.message}")
    except Exception as exc:
        st.error(f"Error inesperado: {exc}")
else:
    nota("Ajusta los parámetros y ejecuta la valoración para ver precio, Greeks y sensibilidad.")

with tab_value:
    seccion("Precio y Greeks")

    if result:
        greeks = result["greeks"]

        c1, c2, c3 = st.columns(3)
        with c1:
            tarjeta_kpi("Precio teórico", _format_money(result["price"]), subtexto="Black-Scholes")
        with c2:
            tarjeta_kpi("Delta", _format_num(greeks["delta"]), subtexto="Sensibilidad al spot")
        with c3:
            tarjeta_kpi("Gamma", _format_num(greeks["gamma"]), subtexto="Curvatura del delta")

        c4, c5, c6 = st.columns(3)
        with c4:
            tarjeta_kpi("Vega", _format_num(greeks["vega"]), subtexto="Sensibilidad a volatilidad")
        with c5:
            tarjeta_kpi("Theta", _format_num(greeks["theta"]), subtexto="Paso del tiempo")
        with c6:
            tarjeta_kpi("Rho", _format_num(greeks["rho"]), subtexto="Sensibilidad a tasas")

        render_meta_row(
            {
                "Tipo": option_type.upper(),
                "Spot": _format_money(spot_price),
                "Strike": _format_money(strike_price),
                "Volatilidad": f"{volatility:.2%}",
                "T": f"{time_to_maturity:.2f} años",
            }
        )
    else:
        render_info_card("Valoración pendiente", "Ejecuta el cálculo para obtener precio teórico y Greeks.")

with tab_payoff:
    seccion("Payoff a vencimiento")

    spot_range = np.linspace(max(0.01, spot_price * 0.45), spot_price * 1.65, 120)
    payoff = np.maximum(spot_range - strike_price, 0) if option_type == "call" else np.maximum(strike_price - spot_range, 0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spot_range, y=payoff, mode="lines", name=f"Payoff {option_type.upper()}"))
    fig.add_vline(x=strike_price, line_dash="dash", annotation_text="Strike")
    fig.add_vline(x=spot_price, line_dash="dot", annotation_text="Spot")

    plot_card_header(
        "Curva de payoff",
        "Valor intrínseco de la opción al vencimiento según el precio del subyacente.",
        modo=modo,
    )
    st.plotly_chart(
        style_plotly_figure(
            fig,
            modo=modo,
            title="Payoff a vencimiento",
            xaxis_title="Precio del subyacente",
            yaxis_title="Payoff",
        ),
        use_container_width=True,
    )
    plot_card_footer("El payoff no incluye el costo inicial de la prima; muestra el valor intrínseco al vencimiento.")

with tab_sensitivity:
    seccion("Sensibilidad a volatilidad")

    if sensitivity_rows:
        sensitivity_df = pd.DataFrame(sensitivity_rows)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=sensitivity_df["Volatilidad"],
                y=sensitivity_df["Precio"],
                mode="markers+lines",
                name="Precio",
            )
        )

        plot_card_header(
            "Precio vs volatilidad",
            "La volatilidad suele aumentar el valor temporal de las opciones.",
            modo=modo,
        )
        st.plotly_chart(
            style_plotly_figure(
                fig,
                modo=modo,
                title="Sensibilidad del precio",
                xaxis_title="Volatilidad",
                yaxis_title="Precio",
            ),
            use_container_width=True,
        )

        st.dataframe(
            sensitivity_df.assign(Volatilidad=sensitivity_df["Volatilidad"].map(lambda x: f"{x:.2%}")),
            use_container_width=True,
            hide_index=True,
        )
    else:
        render_info_card("Sensibilidad pendiente", "Ejecuta la valoración para construir escenarios de volatilidad.")
