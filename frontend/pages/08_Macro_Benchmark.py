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
from ui.page_setup import setup_dashboard_page
from ui.plot_style import style_plotly_figure


BENCHMARK_DEFAULT = "ACWI"
BASE_PORTFOLIO = [
    {"name": "Seven & i Holdings", "ticker": "3382.T", "country": "JP"},
    {"name": "Alimentation Couche-Tard", "ticker": "ATD.TO", "country": "CA"},
    {"name": "FEMSA", "ticker": "FEMSAUBD.MX", "country": "MX"},
    {"name": "BP", "ticker": "BP.L", "country": "UK"},
    {"name": "Carrefour", "ticker": "CA.PA", "country": "FR"},
]


def _fetch_help() -> tuple[dict[str, dict], str | None]:
    client = get_api_client()
    try:
        help_payload = client.get_help_catalog()
        help_map = {item["key"]: item for item in help_payload.get("items", [])}
        return help_map, None
    except ApiClientError:
        return {}, None


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


def _pick_value(payload: dict | None, *keys):
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _normalize_weights(raw_weights: list[float]) -> list[float]:
    total = sum(raw_weights)
    if total <= 0:
        return [1 / len(raw_weights)] * len(raw_weights)
    return [w / total for w in raw_weights]


def _build_compare_payload(
    start: str,
    end: str,
    benchmark_ticker: str,
    weights: list[float],
    base_currency: str,
) -> dict:
    return {
        "tickers": [a["ticker"] for a in BASE_PORTFOLIO],
        "weights": weights,
        "benchmark_ticker": benchmark_ticker,
        "start": start,
        "end": end,
        "base_currency": base_currency,
    }


def _fetch_macro_block(base_currency: str) -> tuple[dict, dict, str | None]:
    client = get_api_client()
    try:
        macro_payload = client.get_macro(base_currency=base_currency)
        fx_payload = client.get_fx_spot(base_currency=base_currency)
        if macro_payload is None:
            macro_payload = {}
        if fx_payload is None:
            fx_payload = {}
        return macro_payload, fx_payload, None
    except ApiClientError as exc:
        return {}, {}, exc.message
    except Exception as exc:
        return {}, {}, f"Error inesperado consultando bloque macro: {exc}"


def _fetch_benchmark_compare(payload: dict) -> tuple[dict, str | None]:
    client = get_api_client()
    try:
        response = client.post_benchmark_compare(payload)
        if response is None:
            return {}, "El endpoint de benchmark respondió vacío."
        if not isinstance(response, dict):
            return {}, f"Respuesta benchmark no válida: {type(response).__name__}"
        return response, None
    except ApiClientError as exc:
        return {}, exc.message
    except Exception as exc:
        return {}, f"Error inesperado consultando benchmark: {exc}"


def _extract_performance_series(payload: dict) -> pd.DataFrame:
    for key in [
        "performance_series",
        "cumulative_series",
        "timeseries",
        "series",
        "chart_data",
        "data",
    ]:
        val = payload.get(key)
        if isinstance(val, list) and val:
            df = pd.DataFrame(val)
            lowered = {c.lower(): c for c in df.columns}

            def pick(*names):
                for n in names:
                    if n in lowered:
                        return lowered[n]
                return None

            date_col = pick("date", "fecha", "timestamp", "datetime")
            port_col = pick("portfolio", "portfolio_index", "portfolio_base100", "portafolio")
            bench_col = pick("benchmark", "benchmark_index", "benchmark_base100", "indice_benchmark")

            if date_col and port_col and bench_col:
                out = pd.DataFrame(
                    {
                        "Fecha": pd.to_datetime(df[date_col], errors="coerce"),
                        "Portafolio": pd.to_numeric(df[port_col], errors="coerce"),
                        "Benchmark": pd.to_numeric(df[bench_col], errors="coerce"),
                    }
                ).dropna()
                if not out.empty:
                    return out.sort_values("Fecha").reset_index(drop=True)

    return pd.DataFrame(columns=["Fecha", "Portafolio", "Benchmark"])


def _extract_summary_table(payload: dict) -> pd.DataFrame:
    rows = [
        {
            "Métrica": "Retorno acumulado portafolio",
            "Valor": _pick_value(payload, "portfolio_cumulative_return", "cumulative_return_portfolio"),
        },
        {
            "Métrica": "Retorno acumulado benchmark",
            "Valor": _pick_value(payload, "benchmark_cumulative_return", "cumulative_return_benchmark"),
        },
        {
            "Métrica": "Retorno anualizado portafolio",
            "Valor": _pick_value(payload, "portfolio_annualized_return", "annualized_return_portfolio"),
        },
        {
            "Métrica": "Retorno anualizado benchmark",
            "Valor": _pick_value(payload, "benchmark_annualized_return", "annualized_return_benchmark"),
        },
        {
            "Métrica": "Volatilidad portafolio",
            "Valor": _pick_value(payload, "portfolio_volatility", "volatility_portfolio"),
        },
        {
            "Métrica": "Volatilidad benchmark",
            "Valor": _pick_value(payload, "benchmark_volatility", "volatility_benchmark"),
        },
        {
            "Métrica": "Sharpe portafolio",
            "Valor": _pick_value(payload, "portfolio_sharpe", "sharpe_portfolio"),
        },
        {
            "Métrica": "Sharpe benchmark",
            "Valor": _pick_value(payload, "benchmark_sharpe", "sharpe_benchmark"),
        },
        {
            "Métrica": "Tracking error",
            "Valor": _pick_value(payload, "tracking_error"),
        },
        {
            "Métrica": "Information ratio",
            "Valor": _pick_value(payload, "information_ratio"),
        },
        {
            "Métrica": "Alpha de Jensen",
            "Valor": _pick_value(payload, "jensen_alpha", "alpha_jensen"),
        },
        {
            "Métrica": "Máximo drawdown portafolio",
            "Valor": _pick_value(payload, "portfolio_max_drawdown", "max_drawdown_portfolio"),
        },
        {
            "Métrica": "Máximo drawdown benchmark",
            "Valor": _pick_value(payload, "benchmark_max_drawdown", "max_drawdown_benchmark"),
        },
    ]

    df = pd.DataFrame(rows)

    def _fmt(v):
        if v is None:
            return "N/D"
        try:
            return f"{float(v):.4f}"
        except Exception:
            return str(v)

    df["Valor"] = df["Valor"].apply(_fmt)
    return df


def _portfolio_weights_table(weights: list[float]) -> pd.DataFrame:
    rows = []
    for asset, weight in zip(BASE_PORTFOLIO, weights):
        rows.append(
            {
                "Activo": asset["name"],
                "Ticker": asset["ticker"],
                "Peso": f"{weight:.2%}",
            }
        )
    return pd.DataFrame(rows)


def _format_pct(v) -> str:
    if v is None:
        return "N/D"
    try:
        return f"{float(v):.2%}"
    except Exception:
        return str(v)


def _format_num(v, ndigits: int = 4) -> str:
    if v is None:
        return "N/D"
    try:
        return f"{float(v):.{ndigits}f}"
    except Exception:
        return str(v)


def _build_relative_performance_figure(
    perf_df: pd.DataFrame,
    modo: str,
    show_portfolio: bool,
    show_benchmark: bool,
    clean_view: bool,
) -> go.Figure:
    fig = go.Figure()

    if not perf_df.empty:
        fig.add_trace(
            go.Scatter(
                x=perf_df["Fecha"],
                y=perf_df["Portafolio"],
                mode="lines",
                name="Portafolio",
                line=dict(width=2.5),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=perf_df["Fecha"],
                y=perf_df["Benchmark"],
                mode="lines",
                name="Benchmark",
                line=dict(width=2.3, dash="dash"),
            )
        )

    for trace in fig.data:
        name = str(getattr(trace, "name", "")).lower()
        if "portafolio" in name or "portfolio" in name:
            trace.visible = True if show_portfolio else "legendonly"
        elif "benchmark" in name:
            trace.visible = True if show_benchmark else "legendonly"

    return style_plotly_figure(
        fig,
        modo=modo,
        title="Rendimiento acumulado base 100",
        xaxis_title="Fecha",
        yaxis_title="Índice base 100",
        show_xgrid=not clean_view,
        show_ygrid=not clean_view,
    )


def _build_macro_panel(macro_payload: dict, fx_payload: dict) -> dict:
    risk_free = _pick_value(
        macro_payload,
        "risk_free_rate",
        "risk_free_rate_annual",
        "rf",
        "rf_annual",
    )
    inflation = _pick_value(
        macro_payload,
        "inflation",
        "inflation_rate",
        "inflation_annual",
    )

    fx_items = []
    if isinstance(fx_payload, dict):
        for key, value in fx_payload.items():
            if isinstance(value, (int, float, str)):
                fx_items.append((key, value))

    return {
        "risk_free": risk_free,
        "inflation": inflation,
        "fx_items": fx_items[:6],
    }


def _reading_text(compare_payload: dict, macro_panel: dict, benchmark_ticker: str) -> str:
    port_ret = _pick_value(compare_payload, "portfolio_cumulative_return", "cumulative_return_portfolio")
    bench_ret = _pick_value(compare_payload, "benchmark_cumulative_return", "cumulative_return_benchmark")
    jensen = _pick_value(compare_payload, "jensen_alpha", "alpha_jensen")
    te = _pick_value(compare_payload, "tracking_error")
    ir = _pick_value(compare_payload, "information_ratio")
    rf = macro_panel["risk_free"]

    return (
        f"Frente al benchmark {benchmark_ticker}, el portafolio acumula {_format_pct(port_ret)} y el benchmark {_format_pct(bench_ret)}. "
        f"El alpha de Jensen se estima en {_format_num(jensen, 4)}, el tracking error en {_format_num(te, 4)} y el information ratio en {_format_num(ir, 4)}. "
        f"La referencia macro usada incluye una tasa libre de riesgo aproximada de {_format_pct(rf)}."
    )


help_map, _ = _fetch_help()

modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros Macro / Benchmark",
    filtros_expanded=False,
)

today = pd.Timestamp.today().normalize()

with filtros_sidebar:
    horizonte = st.selectbox(
        "Horizonte de análisis",
        ["1 mes", "Trimestre", "Semestre", "1 año", "3 años", "5 años", "Personalizado"],
        index=3,
        key="macrobench_horizonte_backend",
    )

    custom_start = None
    custom_end = None
    if horizonte == "Personalizado":
        c1, c2 = st.columns(2)
        with c1:
            custom_start = st.date_input(
                "Fecha inicial",
                value=(today - pd.DateOffset(years=1)).date(),
                max_value=today.date(),
                key="macrobench_custom_start",
            )
        with c2:
            custom_end = st.date_input(
                "Fecha final",
                value=today.date(),
                max_value=today.date(),
                key="macrobench_custom_end",
            )

    benchmark_ticker = st.text_input(
        "Benchmark",
        value=BENCHMARK_DEFAULT,
        key="macrobench_benchmark",
    )

    base_currency = st.selectbox(
        "Moneda base",
        ["USD", "EUR", "COP"],
        index=0,
        key="macrobench_base_currency",
    )

    st.markdown("**Pesos del portafolio**")
    raw_weights = []
    for asset in BASE_PORTFOLIO:
        w = st.slider(
            asset["ticker"],
            min_value=0.0,
            max_value=1.0,
            value=0.20,
            step=0.01,
            key=f"macrobench_weight_{asset['ticker']}",
        )
        raw_weights.append(w)

weights = _normalize_weights(raw_weights)

start_date, end_date = _resolve_dates(
    horizonte=horizonte,
    default_end=today,
    custom_start=pd.Timestamp(custom_start) if custom_start is not None else None,
    custom_end=pd.Timestamp(custom_end) if custom_end is not None else None,
)

if start_date >= end_date:
    st.error("La fecha inicial debe ser menor que la fecha final.")
    st.stop()

macro_payload, fx_payload, macro_error = _fetch_macro_block(base_currency=base_currency)

compare_request = _build_compare_payload(
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
    benchmark_ticker=benchmark_ticker.strip() or BENCHMARK_DEFAULT,
    weights=weights,
    base_currency=base_currency,
)

compare_payload, compare_error = _fetch_benchmark_compare(compare_request)

header_dashboard(
    "Módulo 8 - Macro y benchmark",
    "Conecta contexto macroeconómico y comparación contra benchmark para evaluar desempeño relativo del portafolio",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo integra información macro y compara el portafolio contra el benchmark para contextualizar desempeño, eficiencia y sensibilidad al entorno."
    )
else:
    nota(
        "En modo estadístico se enfatizan métricas relativas frente a benchmark, panel macro, series acumuladas y medidas como Jensen alpha, tracking error e information ratio."
    )

if macro_error:
    st.error(macro_error)
    st.stop()

if compare_error:
    st.error(compare_error)
    st.stop()

if not isinstance(compare_payload, dict) or not compare_payload:
    st.error("No se recibieron datos válidos del endpoint benchmark/compare.")
    st.stop()

macro_panel = _build_macro_panel(macro_payload, fx_payload)
perf_df = _extract_performance_series(compare_payload)
summary_df = _extract_summary_table(compare_payload)
weights_df = _portfolio_weights_table(weights)

render_meta_row(
    [
        ("Benchmark", benchmark_ticker.strip() or BENCHMARK_DEFAULT),
        ("Base", base_currency),
        ("Horizonte", horizonte),
        ("Activos", str(len(BASE_PORTFOLIO))),
    ]
)

seccion("Panel macroeconómico")

m1, m2, m3 = st.columns(3)
with m1:
    tarjeta_kpi(
        "Tasa libre de riesgo",
        _format_pct(macro_panel["risk_free"]),
        subtexto="Referencia macro para evaluación relativa y ratios ajustados por riesgo.",
        help_text="Indicador macro principal usado como tasa base.",
    )
with m2:
    tarjeta_kpi(
        "Inflación",
        _format_pct(macro_panel["inflation"]),
        subtexto="Señal macro del entorno de precios en la moneda base seleccionada.",
        help_text="Ayuda a contextualizar retorno real y presión monetaria.",
    )
with m3:
    tarjeta_kpi(
        "Pares FX spot",
        str(len(macro_panel["fx_items"])),
        subtexto="Cantidad de cotizaciones spot visibles en el panel actual.",
        help_text="Lecturas de tipo de cambio devueltas por el backend.",
    )

if macro_panel["fx_items"]:
    fx_lines = []
    for k, v in macro_panel["fx_items"]:
        fx_lines.append(f"{k}: {v}")
    render_info_card(
        "FX spot",
        " · ".join(fx_lines),
    )
else:
    render_info_card(
        "FX spot",
        "El backend no devolvió cotizaciones spot visibles para esta moneda base.",
    )

seccion("Comparación portafolio vs benchmark")

c1, c2, c3, c4 = st.columns(4)

with c1:
    tarjeta_kpi(
        "Retorno acumulado portafolio",
        _format_pct(_pick_value(compare_payload, "portfolio_cumulative_return", "cumulative_return_portfolio")),
        subtexto="Rendimiento acumulado del portafolio en la ventana seleccionada.",
        help_text="Se compara con benchmark en base 100.",
    )

with c2:
    tarjeta_kpi(
        "Retorno acumulado benchmark",
        _format_pct(_pick_value(compare_payload, "benchmark_cumulative_return", "cumulative_return_benchmark")),
        subtexto="Rendimiento acumulado del benchmark de referencia.",
        help_text="Benchmark principal del proyecto: ACWI.",
    )

with c3:
    tarjeta_kpi(
        "Alpha de Jensen",
        _format_num(_pick_value(compare_payload, "jensen_alpha", "alpha_jensen"), 4),
        subtexto="Exceso de desempeño ajustado por mercado.",
        help_text="Evalúa si el portafolio superó al benchmark en términos ajustados.",
    )

with c4:
    tarjeta_kpi(
        "Information Ratio",
        _format_num(_pick_value(compare_payload, "information_ratio"), 4),
        subtexto="Retorno activo por unidad de tracking error.",
        help_text="Mide consistencia del exceso de retorno frente al benchmark.",
    )

plot_card_footer(_reading_text(compare_payload, macro_panel, benchmark_ticker.strip() or BENCHMARK_DEFAULT))

seccion("Rendimiento acumulado base 100")

plot_card_header(
    "Portafolio vs benchmark",
    "Compara la trayectoria acumulada del portafolio óptimo frente a su benchmark de referencia.",
    modo=modo,
    caption="La serie base 100 facilita lectura relativa de desempeño a lo largo del tiempo.",
)

o1, o2, o3 = st.columns(3)
with o1:
    show_portfolio = st.checkbox("Portafolio", value=True, key="macrobench_show_portfolio")
with o2:
    show_benchmark = st.checkbox("Benchmark", value=True, key="macrobench_show_benchmark")
with o3:
    clean_view = st.checkbox("Vista limpia", value=False, key="macrobench_clean_view")

fig_perf = _build_relative_performance_figure(
    perf_df=perf_df,
    modo=modo,
    show_portfolio=show_portfolio,
    show_benchmark=show_benchmark,
    clean_view=clean_view,
)
st.plotly_chart(fig_perf, width="stretch")
plot_card_footer(
    "La comparación base 100 permite ver si el portafolio supera, empata o queda rezagado frente al benchmark a lo largo del horizonte analizado."
)

seccion("Métricas de desempeño")

if modo == "General":
    with st.expander("Ver tabla de desempeño completa", expanded=False):
        st.dataframe(summary_df, width="stretch", hide_index=True)
else:
    st.dataframe(summary_df, width="stretch", hide_index=True)

seccion("Composición enviada al benchmark")

st.dataframe(weights_df, width="stretch", hide_index=True)

seccion("Interpretación")

render_info_card(
    "Lectura estratégica",
    "Este módulo ayuda a responder si el portafolio superó al benchmark, si el alpha fue positivo, qué tan costoso fue desviarse del índice y cómo el contexto macro puede ayudar a interpretar ese desempeño relativo.",
)