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
from ui.portfolio_state import (
    active_benchmark,
    active_horizon_label,
    active_tickers,
    active_weights_decimal,
    active_weights_pct,
    render_portfolio_scope_note,
)


DEFAULT_TICKERS = ["3382.T", "ATD.TO", "FEMSAUBD.MX", "BP.L", "CA.PA"]
FIXED_INCOME_DURATION_PROXY = {
    "TIP": 6.7,
    "SPIP": 5.0,
    "MUB": 5.8,
    "BNDX": 7.0,
    "BKLN": 0.4,
    "AGG": 6.0,
    "BND": 6.1,
    "IEF": 7.4,
    "TLT": 16.5,
    "SHY": 1.9,
    "LQD": 8.4,
    "HYG": 3.6,
}


def _severity_color(severity: str) -> str:
    return {
        "bajo": "#16A34A",
        "moderado": "#D97706",
        "alto": "#DC2626",
        "critico": "#7F1D1D",
    }.get(str(severity).lower(), "#64748B")


def _default_beta(ticker: str, index: int) -> float:
    seed = sum(ord(char) for char in ticker)
    return round(0.75 + ((seed + index * 7) % 55) / 100.0, 2)


def _build_portfolio(tickers: list[str], weights: list[float]) -> list[dict]:
    if not tickers:
        tickers = DEFAULT_TICKERS

    if not weights or len(weights) != len(tickers):
        weights = [1.0 / len(tickers)] * len(tickers)

    total = sum(float(weight) for weight in weights)
    if total <= 0:
        weights = [1.0 / len(tickers)] * len(tickers)
        total = 1.0

    return [
        {
            "ticker": ticker,
            "weight": float(weight) / total,
            "beta": _default_beta(ticker, index),
            "duration": FIXED_INCOME_DURATION_PROXY.get(ticker.upper()),
        }
        for index, (ticker, weight) in enumerate(zip(tickers, weights))
    ]


def _scenario_specs(include_combined: bool) -> list[dict]:
    scenarios = [
        {"name": "Shock tasa +200 pb", "rate_shock_bp": 200, "market_drop_pct": 0.0, "vol_multiplier": 1.0},
        {"name": "Shock tasa -200 pb", "rate_shock_bp": -200, "market_drop_pct": 0.0, "vol_multiplier": 1.0},
        {"name": "Caida mercado -20%", "rate_shock_bp": 0, "market_drop_pct": -0.20, "vol_multiplier": 1.0},
        {"name": "Caida mercado -30%", "rate_shock_bp": 0, "market_drop_pct": -0.30, "vol_multiplier": 1.0},
        {"name": "Volatilidad x2", "rate_shock_bp": 0, "market_drop_pct": 0.0, "vol_multiplier": 2.0},
    ]
    if include_combined:
        scenarios.append(
            {
                "name": "Tormenta perfecta",
                "rate_shock_bp": 200,
                "market_drop_pct": -0.20,
                "vol_multiplier": 2.0,
            }
        )
    return scenarios


def _scenario_table(scenarios: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Escenario": item["name"],
                "Shock tasa": f"{item['rate_shock_bp']} pb",
                "Shock mercado": format_percent(item["market_drop_pct"]),
                "Volatilidad": f"{format_number(item['vol_multiplier'])}x",
            }
            for item in scenarios
        ]
    )


def _asset_impacts_for_scenario(portfolio: list[dict], scenario: dict) -> list[dict]:
    rate_shock_bp = int(scenario.get("rate_shock_bp", 0))
    market_drop_pct = float(scenario.get("market_drop_pct", 0.0))
    dr = rate_shock_bp / 10_000.0
    impacts = []

    for asset in portfolio:
        duration = asset.get("duration")
        convexity = asset.get("convexity")
        rate_impact = 0.0
        if duration is not None:
            rate_impact = -float(duration) * dr + 0.5 * float(convexity or 0.0) * dr**2

        price_change_pct = float(asset.get("beta", 1.0)) * market_drop_pct + rate_impact
        impacts.append(
            {
                "ticker": asset["ticker"],
                "weight": float(asset["weight"]),
                "beta": float(asset.get("beta", 1.0)),
                "price_change_pct": price_change_pct,
                "contribution_pct": float(asset["weight"]) * price_change_pct,
            }
        )

    return impacts


def _stress_severity(loss_pct: float) -> str:
    loss = abs(float(loss_pct))
    if loss >= 0.20:
        return "critico"
    if loss >= 0.10:
        return "alto"
    if loss >= 0.05:
        return "moderado"
    return "bajo"


def _local_stressed_metric(payload: dict, scenario: dict, weighted_beta: float) -> dict:
    portfolio = payload["portfolio"]
    portfolio_value = float(payload["portfolio_value"])
    base_volatility = float(payload["volatility"])
    base_var_parametric = float(payload["var_parametric_99"])
    base_var_monte_carlo = float(payload["var_monte_carlo_99"])
    vol_multiplier = float(scenario.get("vol_multiplier", 1.0))

    asset_impacts = _asset_impacts_for_scenario(portfolio, scenario)
    portfolio_return = sum(float(item["contribution_pct"]) for item in asset_impacts)
    rate_shock_return = sum(float(item["contribution_pct"]) for item in asset_impacts if abs(float(item["price_change_pct"])) > 0)

    if not asset_impacts:
        market_drop = float(scenario.get("market_drop_pct", 0.0))
        rate_shock = float(scenario.get("rate_shock_bp", 0.0)) / 10_000.0
        portfolio_return = weighted_beta * market_drop - 0.25 * rate_shock
        rate_shock_return = -0.25 * rate_shock

    stressed_value = portfolio_value * (1.0 + portfolio_return)
    loss_amount = max(0.0, portfolio_value - stressed_value)
    loss_pct = loss_amount / portfolio_value if portfolio_value else 0.0
    stressed_volatility = base_volatility * max(vol_multiplier, 0.01)
    stressed_var_parametric = base_var_parametric * max(vol_multiplier, 0.01) + portfolio_return * portfolio_value
    stressed_var_monte_carlo = base_var_monte_carlo * max(vol_multiplier, 0.01) + portfolio_return * portfolio_value

    return {
        "scenario_name": scenario["name"],
        "loss_pct": loss_pct,
        "loss_amount": loss_amount,
        "stressed_portfolio_value": stressed_value,
        "stressed_volatility": stressed_volatility,
        "stressed_var_parametric_99": stressed_var_parametric,
        "stressed_var_monte_carlo_99": stressed_var_monte_carlo,
        "severity": _stress_severity(loss_pct),
        "asset_impacts": asset_impacts,
        "interpretation": (
            "Resultado calculado localmente porque el endpoint de stress no respondio con el contrato nuevo. "
            f"Impacto de mercado/tasa estimado: {format_percent(portfolio_return)}; "
            f"componente sensible a tasa: {format_percent(rate_shock_return)}."
        ),
    }


def _local_stress_result(payload: dict) -> dict:
    portfolio = payload["portfolio"]
    weighted_beta = sum(float(asset["weight"]) * float(asset.get("beta", 1.0)) for asset in portfolio)
    stressed_metrics = [
        _local_stressed_metric(payload, scenario, weighted_beta)
        for scenario in payload["scenarios"]
    ]

    return {
        "base_metrics": {
            "portfolio_value": payload["portfolio_value"],
            "expected_return": payload["expected_return"],
            "volatility": payload["volatility"],
            "var_parametric_99": payload["var_parametric_99"],
            "var_monte_carlo_99": payload["var_monte_carlo_99"],
        },
        "stressed_metrics": stressed_metrics,
    }


def _legacy_stress_result(client, payload: dict) -> dict:
    portfolio = payload["portfolio"]
    weighted_beta = sum(float(asset["weight"]) * float(asset.get("beta", 1.0)) for asset in portfolio)
    stressed_metrics = []

    for scenario in payload["scenarios"]:
        legacy_payload = {
            "portfolio_value": payload["portfolio_value"],
            "expected_return": payload["expected_return"],
            "volatility": payload["volatility"],
            "var_95": -abs(float(payload.get("var_parametric_99", 0.0))),
            "beta": weighted_beta,
            "rate_shock": float(scenario.get("rate_shock_bp", 0)) / 10_000.0,
            "market_shock": float(scenario.get("market_drop_pct", 0.0)),
            "benchmark_shock": float(scenario.get("market_drop_pct", 0.0)),
            "volatility_multiplier": float(scenario.get("vol_multiplier", 1.0)),
        }
        try:
            item = client.post("/stress/scenario", json_payload=legacy_payload, include_api_key=True)
        except ApiClientError:
            stressed_metrics.append(_local_stressed_metric(payload, scenario, weighted_beta))
            continue

        stressed_metrics.append(
            {
                "scenario_name": scenario["name"],
                "loss_pct": item["estimated_loss_pct"],
                "loss_amount": item["estimated_loss"],
                "stressed_portfolio_value": item["stressed_portfolio_value"],
                "stressed_volatility": item["stressed_volatility"],
                "stressed_var_parametric_99": item["stressed_var_95"],
                "stressed_var_monte_carlo_99": item["stressed_var_95"],
                "severity": item["severity"],
                "asset_impacts": _asset_impacts_for_scenario(portfolio, scenario),
                "interpretation": item.get("interpretation", item.get("summary", "")),
            }
        )

    return {
        "base_metrics": {
            "portfolio_value": payload["portfolio_value"],
            "expected_return": payload["expected_return"],
            "volatility": payload["volatility"],
            "var_parametric_99": payload["var_parametric_99"],
            "var_monte_carlo_99": payload["var_monte_carlo_99"],
        },
        "stressed_metrics": stressed_metrics,
    }


def _run_stress(client, payload: dict) -> dict:
    try:
        return client.post("/stress", json_payload=payload, include_api_key=True)
    except ApiClientError as exc:
        if exc.status_code == 404 or "not found" in exc.message.lower():
            return _legacy_stress_result(client, payload)
        return _local_stress_result(payload)
    except Exception:
        return _local_stress_result(payload)


modo, filtros_panel = setup_dashboard_page(
    title="P.R.ED",
    subtitle="Desarrolla Tus Portafolios",
    filtros_label="Parametros de stress testing",
    filtros_expanded=True,
    page_title="Stress Testing",
    page_icon="!",
)

client = get_api_client()
tickers = active_tickers()
weights_pct = active_weights_pct()
weights_decimal = active_weights_decimal()
benchmark_ticker = active_benchmark()
horizon_label = active_horizon_label()
portfolio = _build_portfolio(tickers, weights_decimal)

with filtros_panel:
    render_info_card(
        "Modulo 11 - Stress testing",
        "Aplica escenarios extremos forward-looking al portafolio activo y compara perdida puntual, VaR y sensibilidad por activo.",
    )
    render_portfolio_scope_note()
    render_filter_help(
        "Stress testing vs backtesting",
        "Kupiec valida el VaR contra historia observada; stress testing aplica shocks hipoteticos para anticipar perdidas bajo escenarios adversos.",
    )

    portfolio_value = st.number_input("Valor del portafolio", min_value=1_000.0, value=100_000.0, step=5_000.0)
    expected_return = st.number_input("Retorno esperado base", min_value=-1.0, max_value=1.0, value=0.10, step=0.01, format="%.4f")
    volatility = st.number_input("Volatilidad base", min_value=0.0001, max_value=2.0, value=0.20, step=0.01, format="%.4f")
    var_parametric_99 = st.number_input("VaR parametrico 99% base", min_value=0.0, max_value=2.0, value=0.36, step=0.01, format="%.4f")
    var_monte_carlo_99 = st.number_input("VaR Monte Carlo 99% base", min_value=0.0, max_value=2.0, value=0.42, step=0.01, format="%.4f")
    include_combined = st.checkbox("Incluir tormenta perfecta", value=True)
    run_scenario = st.button("Ejecutar stress testing", type="primary", use_container_width=True)

scenarios = _scenario_specs(include_combined=include_combined)
payload = {
    "portfolio_value": float(portfolio_value),
    "portfolio": portfolio,
    "scenarios": scenarios,
    "expected_return": float(expected_return),
    "volatility": float(volatility),
    "var_parametric_99": float(var_parametric_99),
    "var_monte_carlo_99": float(var_monte_carlo_99),
}

header_dashboard(
    "Mód. 11: Stress testing",
    "Escenarios extremos sobre el portafolio: tasa, mercado, volatilidad y tormenta perfecta.",
    modo=modo,
)

render_meta_row(
    {
        "Activos": ", ".join([asset["ticker"] for asset in portfolio]),
        "Horizonte": horizon_label,
        "Benchmark": benchmark_ticker,
        "Escenarios": str(len(scenarios)),
    }
)

if tickers and weights_pct:
    st.dataframe(
        pd.DataFrame({"Ticker": tickers, "Peso": [format_percent(weight, already_pct=True) for weight in weights_pct]}),
        use_container_width=True,
        hide_index=True,
    )
else:
    nota("No hay portafolio activo en sesión; se usa un portafolio base equiponderado para ilustrar el módulo.")

seccion("Escenarios evaluados")
st.dataframe(_scenario_table(scenarios), use_container_width=True, hide_index=True)

result: dict | None = None
if run_scenario:
    try:
        result = _run_stress(client, payload)
    except ApiClientError as exc:
        st.error(f"Error al consumir backend de stress testing: {exc.message}")
    except Exception as exc:
        st.error(f"Error inesperado: {exc}")
else:
    nota("Ejecuta el stress testing para comparar perdidas, VaR y sensibilidad por activo.")

seccion("Resultado agregado")
if result:
    base = result["base_metrics"]
    stressed = result["stressed_metrics"]
    worst = max(stressed, key=lambda item: float(item["loss_pct"]))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta_kpi("Peor perdida", format_money(worst["loss_amount"]), subtexto=worst["scenario_name"])
    with c2:
        tarjeta_kpi("Perdida %", format_percent(worst["loss_pct"]), subtexto=worst["severity"].upper())
    with c3:
        tarjeta_kpi("VaR 99 base", format_percent(base["var_parametric_99"]), subtexto="Parametrico")
    with c4:
        tarjeta_kpi("VaR 99 peor", format_percent(worst["stressed_var_parametric_99"]), subtexto="Parametrico estresado")

    render_info_card(
        "Lectura ejecutiva",
        "El stress testing aplica shocks hipoteticos al portafolio y muestra donde se concentra la perdida. No reemplaza Kupiec; lo complementa con una mirada forward-looking.",
    )
else:
    render_info_card("Stress pendiente", "Ejecuta el escenario para obtener metricas base y estresadas.")

seccion("Perdida por escenario")
if result:
    stressed = result["stressed_metrics"]
    loss_df = pd.DataFrame(
        [
            {
                "Escenario": item["scenario_name"],
                "Perdida": item["loss_amount"],
                "Perdida_pct": item["loss_pct"],
                "Severidad": item["severity"],
            }
            for item in stressed
        ]
    )
    fig_loss = go.Figure()
    fig_loss.add_trace(
        go.Bar(
            x=loss_df["Escenario"],
            y=loss_df["Perdida"],
            marker_color=[_severity_color(value) for value in loss_df["Severidad"]],
            text=[format_money(value) for value in loss_df["Perdida"]],
            textposition="auto",
            name="Perdida",
        )
    )
    fig_loss.add_hline(y=0, line_dash="dot", annotation_text="Valor base")
    plot_card_header("Bar chart de perdida", "Perdida monetaria estimada para cada escenario obligatorio.", modo=modo)
    st.plotly_chart(
        style_plotly_figure(fig_loss, modo=modo, title="Perdida del portafolio por escenario", xaxis_title="Escenario", yaxis_title="Perdida"),
        use_container_width=True,
    )
    plot_card_footer("La referencia base es perdida cero antes de aplicar shocks.")

    st.dataframe(
        loss_df.assign(Perdida=loss_df["Perdida"].map(format_money), Perdida_pct=loss_df["Perdida_pct"].map(format_percent)),
        use_container_width=True,
        hide_index=True,
    )
else:
    render_info_card("Grafica pendiente", "Ejecuta el stress testing para construir la comparacion por escenario.")

seccion("VaR base vs estresado")
if result:
    base = result["base_metrics"]
    var_df = pd.DataFrame(
        [
            {
                "Escenario": item["scenario_name"],
                "VaR base 99": base["var_parametric_99"],
                "VaR estresado 99": item["stressed_var_parametric_99"],
            }
            for item in result["stressed_metrics"]
        ]
    )
    fig_var = go.Figure()
    fig_var.add_trace(go.Bar(x=var_df["Escenario"], y=var_df["VaR base 99"], name="VaR base 99", marker_color="#2563EB"))
    fig_var.add_trace(go.Bar(x=var_df["Escenario"], y=var_df["VaR estresado 99"], name="VaR estresado 99", marker_color="#DC2626"))
    plot_card_header("Comparacion de VaR", "VaR parametrico al 99% antes y despues del shock.", modo=modo)
    st.plotly_chart(
        style_plotly_figure(fig_var, modo=modo, title="VaR 99 base vs estresado", xaxis_title="Escenario", yaxis_title="VaR"),
        use_container_width=True,
    )
else:
    render_info_card("VaR pendiente", "Ejecuta el stress testing para comparar VaR base y estresado.")

seccion("Heatmap de sensibilidad")
if result:
    rows = []
    for scenario in result["stressed_metrics"]:
        for impact in scenario["asset_impacts"]:
            rows.append(
                {
                    "Escenario": scenario["scenario_name"],
                    "Ticker": impact["ticker"],
                    "Cambio": impact["price_change_pct"],
                }
            )
    heat_df = pd.DataFrame(rows)
    pivot = heat_df.pivot(index="Ticker", columns="Escenario", values="Cambio").fillna(0.0)
    fig_heat = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=list(pivot.columns),
            y=list(pivot.index),
            colorscale="RdYlGn",
            reversescale=False,
            zmid=0,
            text=[[format_percent(value) for value in row] for row in pivot.values],
            texttemplate="%{text}",
            colorbar=dict(title="Delta precio"),
        )
    )
    plot_card_header("Sensibilidad por activo", "Cambio porcentual proyectado de cada activo bajo cada escenario.", modo=modo)
    st.plotly_chart(
        style_plotly_figure(fig_heat, modo=modo, title="Heatmap activo vs escenario", xaxis_title="Escenario", yaxis_title="Activo"),
        use_container_width=True,
    )
    plot_card_footer("Los shocks de mercado se propagan por beta; los shocks de tasa aplican repricing si el activo trae duracion/convexidad.")
else:
    render_info_card("Heatmap pendiente", "Ejecuta el stress testing para ver sensibilidad activo-escenario.")

seccion("Cierre metodologico")
render_info_card(
    "Stress testing vs Kupiec",
    "Kupiec contrasta el VaR con excepciones historicas. Stress testing fuerza escenarios extremos, incluso sin precedente, para estimar perdidas potenciales y preparar decisiones de cobertura o rebalanceo.",
)
