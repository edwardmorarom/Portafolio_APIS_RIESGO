from __future__ import annotations

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


def _format_money(value: float) -> str:
    return f"${float(value):,.2f}"


def _format_pct(value: float) -> str:
    return f"{float(value):.2%}"


setup_dashboard_page(
    page_title="Stress Testing",
    page_icon="⚠️",
)

header_dashboard(
    title="Módulo 11 — Stress testing",
    subtitle="Simulación de escenarios adversos sobre el valor del portafolio.",
)

client = get_api_client()

seccion("Parámetros del escenario")

with st.sidebar:
    st.markdown("### Escenario de stress")

    portfolio_value = st.number_input(
        "Valor del portafolio",
        min_value=1_000.0,
        value=100_000.0,
        step=5_000.0,
    )

    expected_return = st.number_input(
        "Retorno esperado",
        min_value=-1.0,
        max_value=1.0,
        value=0.12,
        step=0.01,
        format="%.4f",
    )

    volatility = st.number_input(
        "Volatilidad base",
        min_value=0.0001,
        max_value=2.0,
        value=0.20,
        step=0.01,
        format="%.4f",
    )

    var_95 = st.number_input(
        "VaR 95%",
        min_value=-1.0,
        max_value=1.0,
        value=-0.08,
        step=0.01,
        format="%.4f",
    )

    beta = st.number_input(
        "Beta del portafolio",
        min_value=-2.0,
        max_value=5.0,
        value=1.15,
        step=0.05,
        format="%.4f",
    )

    rate_shock = st.number_input(
        "Shock de tasa",
        min_value=-1.0,
        max_value=1.0,
        value=0.03,
        step=0.01,
        format="%.4f",
    )

    market_shock = st.number_input(
        "Shock de mercado",
        min_value=-1.0,
        max_value=1.0,
        value=-0.15,
        step=0.01,
        format="%.4f",
    )

    volatility_multiplier = st.number_input(
        "Multiplicador de volatilidad",
        min_value=0.1,
        max_value=10.0,
        value=1.5,
        step=0.1,
        format="%.2f",
    )

payload = {
    "portfolio_value": float(portfolio_value),
    "expected_return": float(expected_return),
    "volatility": float(volatility),
    "var_95": float(var_95),
    "beta": float(beta),
    "rate_shock": float(rate_shock),
    "market_shock": float(market_shock),
    "volatility_multiplier": float(volatility_multiplier),
}

render_info_card(
    "Stress testing",
    "Este módulo estima pérdida potencial bajo shocks de tasa, mercado y volatilidad.",
)

if st.button("Ejecutar escenario", type="primary"):
    try:
        result = client.post("/stress/scenario", json_payload=payload, include_api_key=True)

        seccion("Resultado del escenario")

        col1, col2, col3 = st.columns(3)
        with col1:
            tarjeta_kpi("Pérdida estimada", _format_money(result["estimated_loss"]))
        with col2:
            tarjeta_kpi("Valor estresado", _format_money(result["stressed_portfolio_value"]))
        with col3:
            tarjeta_kpi("Severidad", str(result["severity"]).upper())

        col4, col5, col6 = st.columns(3)
        with col4:
            tarjeta_kpi("Retorno estresado", _format_pct(result["stressed_return"]))
        with col5:
            tarjeta_kpi("Volatilidad estresada", _format_pct(result["stressed_volatility"]))
        with col6:
            tarjeta_kpi("VaR estresado", _format_pct(result["stressed_var_95"]))

        render_meta_row(
            {
                "Shock tasa": _format_pct(rate_shock),
                "Shock mercado": _format_pct(market_shock),
                "Multiplicador vol": f"{volatility_multiplier:.2f}x",
            }
        )

        seccion("Comparación valor base vs estresado")

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=["Valor base", "Valor estresado", "Pérdida estimada"],
                y=[
                    portfolio_value,
                    result["stressed_portfolio_value"],
                    result["estimated_loss"],
                ],
                text=[
                    _format_money(portfolio_value),
                    _format_money(result["stressed_portfolio_value"]),
                    _format_money(result["estimated_loss"]),
                ],
                textposition="auto",
                name="Stress",
            )
        )

        fig.update_layout(
            title="Impacto del escenario de stress",
            xaxis_title="Métrica",
            yaxis_title="Valor monetario",
            showlegend=False,
        )

        plot_card_header("Impacto financiero")
        st.plotly_chart(style_plotly_figure(fig), use_container_width=True)
        plot_card_footer("La gráfica compara el valor inicial del portafolio contra el valor bajo stress.")

        nota(result.get("summary", "Escenario calculado correctamente."))

    except ApiClientError as exc:
        st.error(f"Error al consumir backend de stress testing: {exc.message}")
    except Exception as exc:
        st.error(f"Error inesperado: {exc}")
else:
    nota("Ajusta los parámetros en la barra lateral y ejecuta el escenario de stress.")
