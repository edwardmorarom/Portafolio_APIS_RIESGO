from __future__ import annotations

import pandas as pd
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
from ui.formatting import format_number, format_percent
from ui.page_setup import setup_dashboard_page
from ui.plot_style import style_plotly_figure
from ui.portfolio_state import (
    HORIZON_OPTIONS,
    active_assets,
    active_benchmark,
    active_custom_dates,
    horizon_index,
    render_portfolio_scope_note,
    weights_for_tickers,
)


BASE_PORTFOLIO = [
    {"name": "Seven & i Holdings", "ticker": "3382.T", "country": "JP"},
    {"name": "Alimentation Couche-Tard", "ticker": "ATD.TO", "country": "CA"},
    {"name": "FEMSA", "ticker": "FEMSAUBD.MX", "country": "MX"},
    {"name": "BP", "ticker": "BP.L", "country": "UK"},
    {"name": "Carrefour", "ticker": "CA.PA", "country": "FR"},
]


def _resolve_dates(
    horizonte: str,
    default_end: pd.Timestamp,
    custom_start: pd.Timestamp | None = None,
    custom_end: pd.Timestamp | None = None,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    end_date = default_end.normalize()

    if horizonte == "1 mes":
        start_date = end_date - pd.DateOffset(months=1)
    elif horizonte == "Trimestre":
        start_date = end_date - pd.DateOffset(months=3)
    elif horizonte == "Semestre":
        start_date = end_date - pd.DateOffset(months=6)
    elif horizonte == "1 año":
        start_date = end_date - pd.DateOffset(years=1)
    elif horizonte == "3 años":
        start_date = end_date - pd.DateOffset(years=3)
    elif horizonte == "5 años":
        start_date = end_date - pd.DateOffset(years=5)
    elif horizonte == "Personalizado" and custom_start is not None and custom_end is not None:
        start_date = pd.Timestamp(custom_start).normalize()
        end_date = pd.Timestamp(custom_end).normalize()
    else:
        start_date = end_date - pd.DateOffset(years=1)

    return pd.Timestamp(start_date).normalize(), pd.Timestamp(end_date).normalize()


def _normalize_mode(modo: str) -> str:
    text = str(modo).strip().lower()
    return "estadistico" if text.startswith("estad") else "general"


def _pick_value(payload: dict | None, *keys):
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _format_pct(x) -> str:
    return format_percent(x)


def _format_num(x, ndigits: int = 4) -> str:
    return format_number(x, decimals=ndigits)


def _weights_editor(sidebar_container, selected_assets: list[dict]) -> tuple[list[float], float]:
    with sidebar_container:
        st.markdown("**Pesos del portafolio activo**")
        tickers = [asset["ticker"] for asset in selected_assets]
        weights_decimals, total_pct = weights_for_tickers(tickers)
        weights_pct = [weight * 100.0 for weight in weights_decimals]
        st.dataframe(
            pd.DataFrame({"Ticker": tickers, "Peso": [format_percent(weight, already_pct=True) for weight in weights_pct]}),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Total asignado: {format_percent(total_pct, already_pct=True)}")

        if abs(total_pct - 100.0) > 1e-4:
            st.warning("Los pesos se normalizaron para comparar contra el benchmark.")

    return weights_decimals, 100.0 if weights_decimals else 0.0


def _call_macro_snapshot(client, base_currency: str) -> dict:
    method = getattr(client, "get_macro_snapshot", None)
    if callable(method):
        return method(base_currency=base_currency)

    method = getattr(client, "get_macro", None)
    if callable(method):
        return method(base_currency=base_currency)

    generic = getattr(client, "get", None)
    if callable(generic):
        return generic("/macro", params={"base_currency": base_currency})

    raise RuntimeError("No se encontró método para consultar /macro en api_client.")


def _call_benchmark_compare(client, payload: dict) -> dict:
    method = getattr(client, "post_benchmark_compare", None)
    if callable(method):
        return method(payload)

    method = getattr(client, "compare_benchmark", None)
    if callable(method):
        return method(payload)

    generic = getattr(client, "post", None)
    if callable(generic):
        return generic("/benchmark/compare", json=payload)

    raise RuntimeError("No se encontró método para consultar /benchmark/compare en api_client.")


def _fetch_macro_and_benchmark(
    base_currency: str,
    tickers: list[str],
    benchmark_ticker: str,
    start: str,
    end: str,
    weights: list[float],
    modo: str,
) -> tuple[dict, dict, str | None]:
    client = get_api_client()

    compare_payload = {
        "tickers": tickers,
        "weights": weights,
        "benchmark_ticker": benchmark_ticker,
        "base_currency": base_currency,
        "start": start,
        "end": end,
        "return_type": "log",
        "mode": _normalize_mode(modo),
    }

    try:
        macro_payload = _call_macro_snapshot(client, base_currency=base_currency)
        benchmark_payload = _call_benchmark_compare(client, compare_payload)
        if not isinstance(macro_payload, dict):
            return {}, {}, f"Respuesta macro no válida: {type(macro_payload).__name__}"
        if not isinstance(benchmark_payload, dict):
            return {}, {}, f"Respuesta benchmark no válida: {type(benchmark_payload).__name__}"
        return macro_payload, benchmark_payload, None
    except ApiClientError as exc:
        return {}, {}, exc.message
    except Exception as exc:
        return {}, {}, f"Error inesperado consultando macro/benchmark: {exc}"


def _metric_block(payload: dict, key: str) -> dict:
    val = payload.get(key)
    return val if isinstance(val, dict) else {}


def _extract_macro_table(macro_payload: dict) -> pd.DataFrame:
    candidates = [
        ("Tasa libre de riesgo", _pick_value(macro_payload, "rf_rate_pct", "risk_free_rate_pct", "rate_pct")),
        ("Inflación", _pick_value(macro_payload, "inflation_pct", "inflation", "cpi_yoy_pct")),
        ("Tipo de cambio spot", _pick_value(macro_payload, "fx_spot", "spot_fx", "fx_rate")),
        ("Moneda base", _pick_value(macro_payload, "base_currency")),
        ("Ticker tasa libre", _pick_value(macro_payload, "rf_ticker", "risk_free_ticker")),
    ]
    return pd.DataFrame(candidates, columns=["Indicador", "Valor"])


def _comparison_table(benchmark_payload: dict) -> pd.DataFrame:
    portfolio = _metric_block(benchmark_payload, "portfolio")
    benchmark = _metric_block(benchmark_payload, "benchmark")

    rows = [
        {
            "Métrica": "Rendimiento acumulado",
            "Portafolio": _format_pct(_pick_value(portfolio, "cumulative_return")),
            "Benchmark": _format_pct(_pick_value(benchmark, "cumulative_return")),
        },
        {
            "Métrica": "Rendimiento anualizado",
            "Portafolio": _format_pct(_pick_value(portfolio, "annual_return")),
            "Benchmark": _format_pct(_pick_value(benchmark, "annual_return")),
        },
        {
            "Métrica": "Volatilidad anualizada",
            "Portafolio": _format_pct(_pick_value(portfolio, "annual_volatility")),
            "Benchmark": _format_pct(_pick_value(benchmark, "annual_volatility")),
        },
        {
            "Métrica": "Sharpe",
            "Portafolio": _format_num(_pick_value(portfolio, "sharpe"), 3),
            "Benchmark": _format_num(_pick_value(benchmark, "sharpe"), 3),
        },
        {
            "Métrica": "Máximo drawdown",
            "Portafolio": _format_pct(_pick_value(portfolio, "max_drawdown")),
            "Benchmark": _format_pct(_pick_value(benchmark, "max_drawdown")),
        },
    ]
    return pd.DataFrame(rows)


def _efficiency_conclusion(benchmark_payload: dict) -> str:
    portfolio = _metric_block(benchmark_payload, "portfolio")
    benchmark = _metric_block(benchmark_payload, "benchmark")

    port_ret = _pick_value(portfolio, "annual_return", "cumulative_return")
    bench_ret = _pick_value(benchmark, "annual_return", "cumulative_return")
    port_vol = _pick_value(portfolio, "annual_volatility", "volatility")
    bench_vol = _pick_value(benchmark, "annual_volatility", "volatility")

    if None in (port_ret, bench_ret, port_vol, bench_vol):
        return "No hay métricas suficientes para concluir eficiencia frente al benchmark."

    port_ret = float(port_ret)
    bench_ret = float(bench_ret)
    port_vol = float(port_vol)
    bench_vol = float(bench_vol)

    if port_ret >= bench_ret and port_vol <= bench_vol:
        return "El portafolio luce eficiente: mayor retorno con menor o igual riesgo que el benchmark."
    if port_ret >= bench_ret and port_vol > bench_vol:
        return "El portafolio ofrece más retorno, pero exige aceptar más riesgo que el benchmark."
    if port_ret < bench_ret and port_vol > bench_vol:
        return "El portafolio no luce eficiente frente al benchmark: menor retorno y mayor riesgo."
    return "El portafolio tiene perfil defensivo: menor riesgo, pero también menor retorno que el benchmark."


def _build_base100_chart(benchmark_payload: dict, modo: str, clean_view: bool) -> go.Figure:
    fig = go.Figure()

    port_metrics = _metric_block(benchmark_payload, "portfolio")
    bench_metrics = _metric_block(benchmark_payload, "benchmark")

    port_cum = _pick_value(port_metrics, "cumulative_return")
    bench_cum = _pick_value(bench_metrics, "cumulative_return")

    if port_cum is not None and bench_cum is not None:
        start_label = benchmark_payload.get("start", "Inicio")
        end_label = benchmark_payload.get("end", "Fin")
        x = [start_label, end_label]
        y_port = [100, 100 * (1 + float(port_cum))]
        y_bench = [100, 100 * (1 + float(bench_cum))]

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y_port,
                mode="lines+markers",
                name="Portafolio",
                line=dict(width=3, color="#2563EB"),
                marker=dict(size=8),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y_bench,
                mode="lines+markers",
                name="Benchmark",
                line=dict(width=3, color="#8A1538"),
                marker=dict(size=8),
            )
        )

    fig = style_plotly_figure(
        fig,
        modo=modo,
        title="Portafolio vs benchmark (base 100)",
        xaxis_title="Periodo",
        yaxis_title="Índice base 100",
        show_xgrid=not clean_view,
        show_ygrid=not clean_view,
    )
    fig.update_layout(
        margin=dict(l=24, r=24, t=58, b=24),
        plot_bgcolor="#EEF4FF" if modo == "General" else "#FBEAF1",
    )
    return fig


modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros Macro y Benchmark",
    filtros_expanded=False,
)

today = pd.Timestamp.today().normalize()
portfolio_assets = active_assets() or BASE_PORTFOLIO
stored_custom_start, stored_custom_end = active_custom_dates()
default_custom_start = stored_custom_start or (today - pd.DateOffset(years=1)).date()
default_custom_end = stored_custom_end or today.date()
auto_benchmark = active_benchmark("ACWI")
st.session_state["macro_benchmark_ticker"] = auto_benchmark

with filtros_sidebar:
    render_portfolio_scope_note()

    horizonte = st.selectbox(
        "Horizonte de análisis",
        HORIZON_OPTIONS,
        index=horizon_index(),
        key="macro_benchmark_horizonte",
    )

    custom_start = None
    custom_end = None
    if horizonte == "Personalizado":
        c1, c2 = st.columns(2)
        with c1:
            custom_start = st.date_input(
                "Fecha inicial",
                value=default_custom_start,
                max_value=today.date(),
                key="macro_benchmark_custom_start",
            )
        with c2:
            custom_end = st.date_input(
                "Fecha final",
                value=default_custom_end,
                max_value=today.date(),
                key="macro_benchmark_custom_end",
            )

    benchmark_ticker = st.text_input(
        "Benchmark",
        value=auto_benchmark,
        key="macro_benchmark_ticker",
        disabled=True,
        help="Se define automáticamente según la composición del portafolio activo.",
    )
    base_currency = st.selectbox(
        "Moneda base",
        ["USD"],
        index=0,
        key="macro_benchmark_currency",
        help=(
            "El portafolio se compara en USD porque el backend convierte históricamente "
            "los precios desde su moneda local antes de calcular rendimientos y métricas."
        ),
    )

    weights_decimals, total_pct = _weights_editor(filtros_sidebar, portfolio_assets)

start_date, end_date = _resolve_dates(
    horizonte=horizonte,
    default_end=today,
    custom_start=pd.Timestamp(custom_start) if custom_start is not None else None,
    custom_end=pd.Timestamp(custom_end) if custom_end is not None else None,
)

if start_date >= end_date:
    st.error("La fecha inicial debe ser menor que la fecha final.")
    st.stop()

header_dashboard(
    "Mód. 8: Macro y benchmark",
    "Contextualiza la tasa libre de riesgo y compara el portafolio convertido a USD frente al benchmark global",
    modo=modo,
)

if modo == "General":
    nota(
        "Integra la tasa libre de riesgo, el contexto macroeconómico y la comparación del portafolio frente al benchmark global ACWI. "
        "Las métricas se interpretan en USD porque los activos internacionales fueron convertidos históricamente a una moneda común."
    )
else:
    nota(
        "En modo estadístico se enfatizan Alpha de Jensen, Tracking Error, Information Ratio, Sharpe, drawdown "
        "y el contraste técnico del portafolio contra el benchmark global."
    )

if abs(total_pct - 100.0) > 1e-6:
    st.error("Los pesos del portafolio deben sumar exactamente 100% para comparar contra benchmark.")
    st.stop()

macro_payload, benchmark_payload, fetch_error = _fetch_macro_and_benchmark(
    base_currency=base_currency,
    tickers=[asset["ticker"] for asset in portfolio_assets],
    benchmark_ticker=benchmark_ticker.strip() or "ACWI",
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
    weights=weights_decimals,
    modo=modo,
)

if fetch_error:
    st.error(fetch_error)
    st.stop()

portfolio = _metric_block(benchmark_payload, "portfolio")
benchmark = _metric_block(benchmark_payload, "benchmark")

alpha_jensen = _pick_value(benchmark_payload, "alpha_jensen")
tracking_error = _pick_value(benchmark_payload, "tracking_error")
information_ratio = _pick_value(benchmark_payload, "information_ratio")
rf_rate_pct = _pick_value(benchmark_payload, "rf_rate_pct", "risk_free_rate_pct")
rf_ticker = _pick_value(benchmark_payload, "rf_ticker", "risk_free_ticker")
summary = _pick_value(benchmark_payload, "summary")

render_meta_row(
    [
        ("Benchmark", benchmark_ticker.strip() or "ACWI"),
        ("Moneda base", "USD"),
        ("Rf usada", _format_pct((float(rf_rate_pct) / 100.0) if rf_rate_pct is not None else None)),
        ("Ticker Rf", str(rf_ticker or "N/D")),
        ("Horizonte", horizonte),
    ]
)

seccion("Panel macroeconómico")

k1, k2, k3 = st.columns(3)
with k1:
    tarjeta_kpi(
        "Tasa libre de riesgo",
        _format_pct((float(rf_rate_pct) / 100.0) if rf_rate_pct is not None else None),
        subtexto=f"Referencia usada para Sharpe y Alpha de Jensen. Fuente: {rf_ticker or 'N/D'}.",
        help_text=(
            "La tasa libre de riesgo representa el retorno de referencia con riesgo mínimo. "
            "En este proyecto se usa una Rf en USD porque el portafolio fue convertido históricamente a dólares."
        ),
    )
inflation_value = _pick_value(macro_payload, "inflation_pct", "inflation_yoy", "inflation", "cpi_yoy_pct")
fx_value = _pick_value(macro_payload, "fx_spot", "spot_fx", "fx_rate")

with k2:
    tarjeta_kpi(
        "Inflación",
        _format_pct(float(inflation_value) / 100.0) if inflation_value is not None else "No disponible",
        subtexto=(
            "Inflación anual YoY desde FRED CPIAUCSL."
            if inflation_value is not None
            else "No disponible: falta FRED_API_KEY o FRED no respondió."
        ),
        help_text=(
            "La inflación se calcula desde FRED usando CPIAUCSL cuando existe una API key configurada. "
            "Si no hay FRED_API_KEY, el sistema no inventa el dato y lo reporta como no disponible."
        ),
    )

with k3:
    if fx_value is not None:
        tarjeta_kpi(
            "Spot FX",
            _format_num(fx_value, 4),
            subtexto="Tipo de cambio de referencia para la moneda base.",
        )
    else:
        tarjeta_kpi(
            "Spot FX",
            "No disponible",
            subtexto="El endpoint macro no devolvió este indicador.",
        )

render_info_card(
    "Lectura macro",
    (
        "El panel macro resume la tasa libre de riesgo, inflación y referencia cambiaria. "
        "Como el portafolio contiene activos de varios países, el backend convierte históricamente los precios a USD "
        "para que la comparación contra ACWI sea homogénea. La tasa libre de riesgo se usa como referencia para Sharpe, "
        "Alpha de Jensen y otras métricas ajustadas por riesgo."
    ),
)


seccion("Comparación contra benchmark")

c1, c2, c3 = st.columns(3)
with c1:
    tarjeta_kpi(
        "Alpha de Jensen",
        _format_pct(alpha_jensen),
        subtexto="Exceso de retorno frente al CAPM aplicado al benchmark.",
        help_text=(
            "Alpha de Jensen mide si el portafolio obtuvo más o menos retorno del esperado "
            "según su riesgo sistemático frente al benchmark."
        ),
    )

with c2:
    tarjeta_kpi(
        "Tracking Error",
        _format_pct(tracking_error),
        subtexto="Desviación anualizada de retornos activos.",
        help_text=(
            "Tracking Error mide qué tan diferente se mueve el portafolio respecto al benchmark. "
            "Un valor alto indica mayor desviación frente a la referencia."
        ),
    )

with c3:
    tarjeta_kpi(
        "Information Ratio",
        _format_num(information_ratio, 3),
        subtexto="Retorno activo por unidad de tracking error.",
        help_text=(
            "Information Ratio mide si el exceso de retorno frente al benchmark compensa "
            "la desviación asumida respecto a esa referencia."
        ),
    )

plot_card_header(
    "Tabla de eficiencia frente al benchmark",
    (
        "Compara retorno, volatilidad, Sharpe y riesgo del portafolio contra su referencia automática."
    ),
    modo=modo,
    caption="La lectura se centra en eficiencia financiera, no solo en desempeño acumulado.",
)

st.dataframe(_comparison_table(benchmark_payload), use_container_width=True, hide_index=True)
plot_card_footer(_efficiency_conclusion(benchmark_payload))

seccion("Interpretación")

render_info_card(
    "Resumen interpretativo",
    str(summary)
    if summary
    else (
        "El portafolio se compara contra ACWI usando métricas relativas. "
        "Alpha de Jensen permite evaluar desempeño ajustado por riesgo sistemático; "
        "Tracking Error mide qué tanto se desvía el portafolio del benchmark; "
        "e Information Ratio resume si el exceso de retorno compensa esa desviación."
    ),
)
