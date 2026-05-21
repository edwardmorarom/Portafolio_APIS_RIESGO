from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_filters import render_filter_help
from ui.dashboard_ui import header_dashboard, nota, plot_card_footer, plot_card_header, seccion, tarjeta_kpi
from ui.formatting import format_money, format_number, format_percent
from ui.page_setup import setup_dashboard_page
from ui.plot_style import style_plotly_figure
from ui.portfolio_state import active_benchmark, active_horizon_label, active_tickers, active_weights_pct, render_portfolio_scope_note


def _severity_color(severity: str) -> str:
    return {"bajo": "#16A34A", "moderado": "#D97706", "alto": "#DC2626", "critico": "#7F1D1D"}.get(str(severity).lower(), "#64748B")


def _scenario_defaults(name: str) -> dict[str, float]:
    scenarios = {
        "Caida mercado": {"rate_shock": 0.01, "market_shock": -0.20, "benchmark_shock": -0.20, "volatility_multiplier": 1.8},
        "Shock tasas": {"rate_shock": 0.02, "market_shock": -0.08, "benchmark_shock": -0.10, "volatility_multiplier": 1.3},
        "Volatilidad extrema": {"rate_shock": 0.00, "market_shock": -0.12, "benchmark_shock": -0.15, "volatility_multiplier": 2.2},
        "Combinado severo": {"rate_shock": 0.03, "market_shock": -0.25, "benchmark_shock": -0.25, "volatility_multiplier": 2.5},
    }
    return scenarios.get(name, scenarios["Caida mercado"])


modo, filtros_panel = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomas",
    filtros_label="Parametros de stress testing",
    filtros_expanded=True,
    page_title="Stress Testing",
    page_icon="!",
)

client = get_api_client()
tickers = active_tickers()
weights_pct = active_weights_pct()
benchmark_ticker = active_benchmark()
horizon_label = active_horizon_label()

with filtros_panel:
    render_portfolio_scope_note()
    render_filter_help(
        "Como llenar stress testing",
        "Elige un escenario adverso y ajusta shocks. Valores negativos en mercado/benchmark representan caida; multiplicador de volatilidad mayor a 1 amplifica incertidumbre.",
    )
    scenario_name = st.radio(
        "Escenario",
        ["Caida mercado", "Shock tasas", "Volatilidad extrema", "Combinado severo"],
        horizontal=True,
        key="stress_scenario_name",
        help="Selecciona una combinacion base de shocks adversos. Puedes ajustar cada shock manualmente despues.",
    )
    defaults = _scenario_defaults(scenario_name)
    c1, c2 = st.columns(2)
    with c1:
        portfolio_value = st.number_input("Valor del portafolio", min_value=1_000.0, value=100_000.0, step=5_000.0, help="Monto que se estresa bajo el escenario adverso.")
        expected_return = st.number_input("Retorno esperado", min_value=-1.0, max_value=1.0, value=0.12, step=0.01, format="%.4f", help="Retorno base antes de aplicar shocks de mercado y tasa.")
        volatility = st.number_input("Volatilidad base", min_value=0.0001, max_value=2.0, value=0.20, step=0.01, format="%.4f", help="Incertidumbre anualizada del portafolio antes del escenario.")
        var_95 = st.number_input("VaR 95%", min_value=-1.0, max_value=1.0, value=-0.08, step=0.01, format="%.4f", help="Perdida extrema base usada para construir el VaR estresado.")
    with c2:
        beta = st.number_input("Beta del portafolio", min_value=-2.0, max_value=5.0, value=1.15, step=0.05, format="%.4f", help="Sensibilidad del portafolio frente al benchmark.")
        rate_shock = st.number_input("Shock de tasa", min_value=-1.0, max_value=1.0, value=float(defaults["rate_shock"]), step=0.01, format="%.4f", help="Aumento o caida de tasas que afecta el retorno estresado.")
        market_shock = st.number_input("Shock de mercado", min_value=-1.0, max_value=1.0, value=float(defaults["market_shock"]), step=0.01, format="%.4f", help="Caida o subida del mercado aplicada segun beta.")
        benchmark_shock = st.number_input(f"Shock benchmark {benchmark_ticker}", min_value=-1.0, max_value=1.0, value=float(defaults["benchmark_shock"]), step=0.01, format="%.4f", help="Shock usado para comparar la perdida del portafolio contra su benchmark.")
        volatility_multiplier = st.number_input("Multiplicador de volatilidad", min_value=0.1, max_value=10.0, value=float(defaults["volatility_multiplier"]), step=0.1, format="%.2f", help="Factor que amplifica o reduce volatilidad y VaR bajo estres.")
    run_scenario = st.button("Ejecutar escenario", type="primary", use_container_width=True)

payload = {
    "portfolio_value": float(portfolio_value),
    "expected_return": float(expected_return),
    "volatility": float(volatility),
    "var_95": float(var_95),
    "beta": float(beta),
    "rate_shock": float(rate_shock),
    "market_shock": float(market_shock),
    "benchmark_shock": float(benchmark_shock),
    "volatility_multiplier": float(volatility_multiplier),
}

header_dashboard("Stress testing", "Simulacion de escenarios adversos de tasa, mercado y volatilidad sobre el portafolio.", modo=modo)

render_meta_row({"Activos": ", ".join(tickers) if tickers else "N/D", "Horizonte": horizon_label, "Benchmark": benchmark_ticker, "Escenario": scenario_name})

if tickers and weights_pct:
    st.dataframe(pd.DataFrame({"Ticker": tickers, "Peso": [format_percent(weight, already_pct=True) for weight in weights_pct]}), use_container_width=True, hide_index=True)

result: dict | None = None
if run_scenario:
    try:
        result = client.post("/stress/scenario", json_payload=payload, include_api_key=True)
    except ApiClientError as exc:
        st.error(f"Error al consumir backend de stress testing: {exc.message}")
    except Exception as exc:
        st.error(f"Error inesperado: {exc}")
else:
    nota("Ajusta el escenario y ejecutalo para estimar perdida, valor estresado y severidad.")

seccion("Resultado del escenario")
if result:
    severity = str(result["severity"]).lower()
    benchmark_loss_pct = result.get("benchmark_loss_pct")
    if benchmark_loss_pct is None:
        benchmark_loss_pct = max(0.0, -float(benchmark_shock if benchmark_shock is not None else market_shock))
    relative_to_benchmark = result.get("relative_to_benchmark")
    if not relative_to_benchmark:
        relative_to_benchmark = "mejor defensa que el benchmark" if float(result.get("estimated_loss_pct", 0.0)) < float(benchmark_loss_pct) else "menor eficiencia defensiva que el benchmark"

    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta_kpi("Perdida estimada", format_money(result["estimated_loss"]), subtexto="Perdida monetaria", help_text="Monto que podria perder el portafolio bajo el escenario adverso.")
    with c2:
        tarjeta_kpi("Valor estresado", format_money(result["stressed_portfolio_value"]), subtexto="Valor post-shock", help_text="Valor restante despues de descontar la perdida estimada.")
    with c3:
        tarjeta_kpi("Severidad", severity.upper(), subtexto="Clasificacion del escenario", help_text="Clasificacion simple segun el porcentaje de perdida estimada.")

    c4, c5, c6 = st.columns(3)
    with c4:
        tarjeta_kpi("Retorno stress", format_percent(result["stressed_return"]), subtexto="Retorno ajustado", help_text="Retorno esperado despues de aplicar shocks de mercado y tasa.")
    with c5:
        tarjeta_kpi("Volatilidad stress", format_percent(result["stressed_volatility"]), subtexto="Volatilidad ampliada", help_text="Volatilidad base multiplicada por el factor de estres.")
    with c6:
        tarjeta_kpi("VaR stress", format_percent(result["stressed_var_95"]), subtexto="VaR bajo shock", help_text="VaR recalculado como perdida extrema bajo condiciones adversas.")

    render_meta_row(
        {
            "Shock tasa": format_percent(rate_shock),
            "Shock mercado": format_percent(market_shock),
            f"Shock {benchmark_ticker}": format_percent(benchmark_shock),
            "Multiplicador vol": f"{format_number(volatility_multiplier)}x",
            "Beta": format_number(beta),
        }
    )
    render_info_card("Interpretacion automatica", result.get("interpretation", result.get("summary", "")))
else:
    render_info_card("Escenario pendiente", "Ejecuta el escenario para obtener los indicadores de stress.")

seccion("Impacto financiero")
if result:
    severity = str(result["severity"]).lower()
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=["Valor base", "Valor estresado", "Perdida"],
            y=[portfolio_value, result["stressed_portfolio_value"], result["estimated_loss"]],
            marker_color=["#2563EB", _severity_color(severity), "#DC2626"],
            text=[format_money(portfolio_value), format_money(result["stressed_portfolio_value"]), format_money(result["estimated_loss"])],
            textposition="auto",
            name="Stress",
        )
    )
    plot_card_header("Impacto financiero", "Compara el valor inicial contra la perdida estimada y el valor restante bajo estres.", modo=modo)
    st.plotly_chart(style_plotly_figure(fig, modo=modo, title="Valor bajo stress", xaxis_title="Metrica", yaxis_title="Valor monetario", show_xgrid=False), use_container_width=True)
    plot_card_footer("La barra de perdida estima el dano combinado de shocks de retorno y VaR estresado.")
    st.dataframe(
        pd.DataFrame(
            [
                {"Metrica": "Perdida portafolio", "Valor": format_percent(result.get("estimated_loss_pct", 0.0))},
                {"Metrica": f"Perdida benchmark {benchmark_ticker}", "Valor": format_percent(benchmark_loss_pct)},
                {"Metrica": "Lectura relativa", "Valor": relative_to_benchmark},
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
else:
    render_info_card("Impacto pendiente", "Ejecuta el escenario para ver la comparacion grafica.")

seccion("Lectura ejecutiva")
render_info_card(
    "Uso financiero",
    "El stress testing no predice el futuro: fuerza una combinacion adversa de mercado, tasas y volatilidad para evaluar resiliencia, cobertura, rebalanceo o liquidez.",
)
if result:
    nota(result.get("interpretation") or result.get("summary", "Escenario calculado correctamente."))
