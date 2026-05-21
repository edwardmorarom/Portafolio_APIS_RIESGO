from __future__ import annotations

import numpy as np
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
BASE_CURRENCY_DEFAULT = "USD"

PORTFOLIO_ASSETS = [
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


def _pick_value(payload: dict | None, *keys):
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _asset_options() -> tuple[list[str], dict[str, dict]]:
    labels = []
    asset_map: dict[str, dict] = {}
    for asset in PORTFOLIO_ASSETS:
        label = f"{asset['name']} · {asset['ticker']} · {asset['country']}"
        labels.append(label)
        asset_map[label] = asset
    return labels, asset_map


def _weights_editor(sidebar_container, key_prefix: str) -> tuple[list[float], float]:
    with sidebar_container:
        st.markdown("**Pesos del portafolio (%)**")
        weights_pct: list[float] = []
        for asset in PORTFOLIO_ASSETS:
            value = st.number_input(
                asset["ticker"],
                min_value=0.0,
                max_value=100.0,
                value=20.0,
                step=1.0,
                key=f"{key_prefix}_{asset['ticker']}",
                format="%.2f",
            )
            weights_pct.append(float(value))

        total_pct = float(sum(weights_pct))
        st.caption(f"Total asignado: {total_pct:.2f}%")

        if total_pct > 100.0 + 1e-6:
            st.error("Los pesos no pueden superar 100%.")
        elif abs(total_pct - 100.0) > 1e-6:
            st.warning("Para calcular el CAPM del portafolio, los pesos deben sumar exactamente 100%.")

    return [w / 100.0 for w in weights_pct], total_pct


def _fetch_capm(
    ticker: str,
    start: str,
    end: str,
    benchmark_ticker: str,
    base_currency: str,
    return_type: str = "log",
) -> tuple[dict, str | None]:
    client = get_api_client()
    try:
        payload = client.get_capm(
            ticker=ticker,
            start=start,
            end=end,
            benchmark_ticker=benchmark_ticker,
            base_currency=base_currency,
            return_type=return_type,
            mode="general",
        )
        return payload, None
    except ApiClientError as exc:
        return {}, exc.message
    except Exception as exc:
        return {}, f"Error inesperado consultando CAPM: {exc}"


def _fetch_portfolio_capm(
    tickers: list[str],
    weights: list[float],
    benchmark_ticker: str,
    base_currency: str,
    start: str,
    end: str,
    return_type: str = "log",
) -> tuple[dict, str | None]:
    client = get_api_client()
    payload = {
        "tickers": tickers,
        "weights": weights,
        "benchmark_ticker": benchmark_ticker,
        "base_currency": base_currency,
        "start": start,
        "end": end,
        "return_type": return_type,
    }

    try:
        response = client.get_portfolio_capm(payload)
        if response is None:
            return {}, "El endpoint CAPM de portafolio respondió vacío."
        if not isinstance(response, dict):
            return {}, f"Respuesta CAPM portafolio no válida: {type(response).__name__}"
        return response, None
    except ApiClientError as exc:
        return {}, exc.message
    except Exception as exc:
        return {}, f"Error inesperado consultando CAPM del portafolio: {exc}"


def _coerce_series_frame(payload: dict) -> pd.DataFrame:
    for key in ["regression_points", "scatter", "points", "data", "regression_data"]:
        val = payload.get(key)
        if isinstance(val, list) and val:
            df = pd.DataFrame(val)
            lowered = {c.lower(): c for c in df.columns}

            def pick(*names):
                for n in names:
                    if n in lowered:
                        return lowered[n]
                return None

            x_col = pick("benchmark_excess", "x", "benchmark", "market_excess")
            y_col = pick("asset_excess", "y", "asset", "security_excess")

            if x_col and y_col:
                out = pd.DataFrame(
                    {
                        "benchmark_excess": pd.to_numeric(df[x_col], errors="coerce"),
                        "asset_excess": pd.to_numeric(df[y_col], errors="coerce"),
                    }
                ).dropna()
                if not out.empty:
                    return out

    return pd.DataFrame(columns=["benchmark_excess", "asset_excess"])


def _build_regression_figure(
    points_df: pd.DataFrame,
    modo: str,
    show_points: bool,
    show_line: bool,
    clean_view: bool,
) -> go.Figure:
    fig = go.Figure()

    if not points_df.empty:
        x_vals = pd.to_numeric(points_df["benchmark_excess"], errors="coerce").dropna()
        y_vals = pd.to_numeric(points_df["asset_excess"], errors="coerce").dropna()

        fig.add_trace(
            go.Scatter(
                x=points_df["benchmark_excess"],
                y=points_df["asset_excess"],
                mode="markers",
                name="Observaciones",
                marker=dict(size=7, opacity=0.72, color="#4F73FF"),
            )
        )

        if len(x_vals) >= 2 and len(y_vals) >= 2:
            slope, intercept = np.polyfit(x_vals, y_vals, 1)
            x_line = pd.Series([float(x_vals.min()), float(x_vals.max())])
            y_line = intercept + slope * x_line

            fig.add_trace(
                go.Scatter(
                    x=x_line,
                    y=y_line,
                    mode="lines",
                    name="Regresión",
                    line=dict(width=2.6, color="#8A1538"),
                )
            )

    for trace in fig.data:
        name = str(getattr(trace, "name", "")).lower()
        if "observ" in name:
            trace.visible = True if show_points else "legendonly"
        elif "regresi" in name:
            trace.visible = True if show_line else "legendonly"

    fig = style_plotly_figure(
        fig,
        modo=modo,
        title="Regresión CAPM",
        xaxis_title="Exceso Benchmark",
        yaxis_title="Exceso Activo",
        show_xgrid=not clean_view,
        show_ygrid=not clean_view,
    )
    fig.update_layout(margin=dict(l=70, r=34, t=110, b=64))
    return fig


def _format_capm_table(payload: dict) -> pd.DataFrame:
    rows = [
        {"metric": "beta", "value": _pick_value(payload, "beta")},
        {"metric": "alpha_simple", "value": _pick_value(payload, "alpha_simple", "alpha_daily", "alpha")},
        {"metric": "r_squared", "value": _pick_value(payload, "r_squared", "r2")},
        {"metric": "p_value_beta", "value": _pick_value(payload, "p_value_beta", "beta_p_value")},
        {
            "metric": "capm_expected_return",
            "value": _pick_value(payload, "capm_expected_return", "expected_return_annual", "expected_return"),
        },
        {"metric": "classification", "value": _pick_value(payload, "classification")},
        {"metric": "rf_rate_pct", "value": _pick_value(payload, "rf_rate_pct", "rf_annual")},
    ]
    df = pd.DataFrame(rows)

    def _fmt(v):
        if v is None:
            return "N/D"
        try:
            if pd.isna(v):
                return "N/D"
        except Exception:
            pass
        try:
            return f"{float(v):.10f}"
        except Exception:
            return str(v)

    df["value"] = df["value"].apply(_fmt)
    return df


def _classify_beta(beta: float | None) -> str:
    if beta is None:
        return "Sin clasificación"
    if beta < 0.8:
        return "Defensivo"
    if beta <= 1.2:
        return "Neutro"
    return "Agresivo"


def _expected_return_text(v) -> str:
    if v is None:
        return "N/D"
    try:
        if pd.isna(v):
            return "N/D"
    except Exception:
        pass
    return f"{float(v):.2%}"


def _format_num(x, ndigits: int = 4) -> str:
    if x is None:
        return "N/D"
    try:
        return f"{float(x):.{ndigits}f}"
    except Exception:
        return str(x)


def _capm_reading(payload: dict) -> str:
    beta = _pick_value(payload, "beta")
    alpha = _pick_value(payload, "alpha_simple", "alpha_daily", "alpha")
    r2 = _pick_value(payload, "r_squared", "r2")
    exp_ret = _pick_value(payload, "capm_expected_return", "expected_return_annual", "expected_return")
    rf = _pick_value(payload, "rf_rate_pct", "rf_annual")

    beta_text = f"{float(beta):.4f}" if beta is not None else "N/D"
    alpha_text = f"{float(alpha):.6f}" if alpha is not None else "N/D"
    r2_text = f"{float(r2):.4f}" if r2 is not None else "N/D"
    rf_text = f"{float(rf) / 100:.2%}" if rf is not None else "N/D"

    return (
        f"La beta de {beta_text} resume la sensibilidad del activo frente al benchmark, "
        f"el alpha simple es {alpha_text}, el R² del ajuste es {r2_text} "
        f"y el retorno esperado por CAPM es {_expected_return_text(exp_ret)} con tasa libre de riesgo de {rf_text}."
    )


modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros CAPM",
    filtros_expanded=False,
)

today = pd.Timestamp.today().normalize()
asset_labels, asset_map = _asset_options()

with filtros_sidebar:
    selected_label = st.selectbox(
        "Activo",
        options=asset_labels,
        key="capm_asset_backend",
    )

    horizonte = st.selectbox(
        "Horizonte de análisis",
        ["1 mes", "Trimestre", "Semestre", "1 año", "3 años", "5 años", "Personalizado"],
        index=3,
        key="capm_horizonte_backend",
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
                key="capm_custom_start",
            )
        with c2:
            custom_end = st.date_input(
                "Fecha final",
                value=today.date(),
                max_value=today.date(),
                key="capm_custom_end",
            )

    benchmark_ticker = st.text_input("Benchmark", value=BENCHMARK_DEFAULT, key="capm_benchmark")
    base_currency = st.selectbox("Moneda base", ["USD", "EUR", "COP"], index=0, key="capm_base_currency")

    weights_decimals, total_pct = _weights_editor(filtros_sidebar, "capm_weight")

selected_asset = asset_map[selected_label]
ticker = selected_asset["ticker"]
asset_name = selected_asset["name"]

start_date, end_date = _resolve_dates(
    horizonte=horizonte,
    default_end=today,
    custom_start=pd.Timestamp(custom_start) if custom_start is not None else None,
    custom_end=pd.Timestamp(custom_end) if custom_end is not None else None,
)

if start_date >= end_date:
    st.error("La fecha inicial debe ser menor que la fecha final.")
    st.stop()

payload, capm_error = _fetch_capm(
    ticker=ticker,
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
    benchmark_ticker=benchmark_ticker.strip() or BENCHMARK_DEFAULT,
    base_currency=base_currency,
)

portfolio_payload = {}
portfolio_capm_error = None
if abs(total_pct - 100.0) <= 1e-6:
    portfolio_payload, portfolio_capm_error = _fetch_portfolio_capm(
        tickers=[a["ticker"] for a in PORTFOLIO_ASSETS],
        weights=weights_decimals,
        benchmark_ticker=benchmark_ticker.strip() or BENCHMARK_DEFAULT,
        base_currency=base_currency,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
    )

header_dashboard(
    "Mód. 4: CAPM, Beta y Riesgo Sistemático",
    "Cuantifica la sensibilidad del activo y del portafolio frente al benchmark global en USD.",
    modo=modo,
)       

if modo == "General":
    nota(
        "Incluye beta del activo, beta del portafolio, regresión frente al benchmark ACWI y retorno esperado bajo CAPM. "
        "Los retornos se interpretan en USD porque el backend convierte históricamente los precios desde su moneda local."
    )
else:
    nota(
        "En modo estadístico se enfatizan la regresión CAPM, R², alpha, p-value de beta, clasificación del activo "
        "y comparación entre beta individual y beta del portafolio."
    )

if capm_error:
    st.error(capm_error)
    st.stop()

if portfolio_capm_error:
    st.warning(f"No fue posible cargar beta del portafolio: {portfolio_capm_error}")

beta = _pick_value(payload, "beta")
alpha_simple = _pick_value(payload, "alpha_simple", "alpha_daily", "alpha")
r_squared = _pick_value(payload, "r_squared", "r2")
expected_return_annual = _pick_value(payload, "capm_expected_return", "expected_return_annual", "expected_return")
classification = _pick_value(payload, "classification") or _classify_beta(beta)
points_df = _coerce_series_frame(payload)
table_df = _format_capm_table(payload)

portfolio_beta = _pick_value(portfolio_payload, "portfolio_beta", "beta")
portfolio_return_annual = _pick_value(portfolio_payload, "portfolio_return_annual", "expected_return_annual")
portfolio_capm_expected = _pick_value(portfolio_payload, "capm_expected_return", "expected_return")
portfolio_alpha = _pick_value(portfolio_payload, "alpha_simple", "alpha")

render_meta_row(
    [
        ("Activo", asset_name),
        ("Ticker", ticker),
        ("Benchmark", benchmark_ticker.strip() or BENCHMARK_DEFAULT),
        ("Moneda base", "USD"),
        ("Rf", base_currency),
        ("Horizonte", horizonte),
    ]
)

seccion("KPIs CAPM")

if portfolio_beta is not None:
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        tarjeta_kpi("Beta del portafolio", _format_num(portfolio_beta, 4), subtexto="Sensibilidad conjunta de la cartera.")
    with p2:
        tarjeta_kpi("Retorno anual portafolio", _expected_return_text(portfolio_return_annual), subtexto="Rentabilidad anualizada de la cartera.")
    with p3:
        tarjeta_kpi("Retorno CAPM portafolio", _expected_return_text(portfolio_capm_expected), subtexto="Retorno esperado bajo CAPM.")
    with p4:
        tarjeta_kpi("Alpha portafolio", _format_num(portfolio_alpha, 6), subtexto="Desviación frente al retorno esperado.")

    render_info_card(
        "Lectura del portafolio",
    (
        f"La beta del portafolio es {_format_num(portfolio_beta, 4)}. "
        "Esta medida resume la sensibilidad conjunta de la cartera frente al benchmark global. "
        "Si la beta es mayor que 1, el portafolio tiende a amplificar los movimientos del mercado; "
        "si es menor que 1, se comporta de forma más defensiva. "
        "La beta del portafolio complementa la beta individual del activo seleccionado."
    ),
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    tarjeta_kpi(
        "Beta",
        _format_num(beta, 4),
        subtexto="Sensibilidad sistemática frente al mercado.",
        help_text=(
            "Beta mide cuánto se mueve el activo frente al benchmark. "
            "Beta mayor a 1 indica mayor sensibilidad; beta menor a 1 indica comportamiento más defensivo."
        ),
    )

with c2:
    tarjeta_kpi(
        "Alpha simple",
        _format_num(alpha_simple, 6),
        subtexto="Exceso de retorno no explicado por la beta.",
        help_text=(
            "Alpha mide la parte del retorno que no queda explicada por el movimiento del benchmark. "
            "Un alpha positivo sugiere desempeño superior al esperado por CAPM."
        ),
    )

with c3:
    tarjeta_kpi(
        "R²",
        _format_num(r_squared, 4),
        subtexto="Capacidad explicativa del ajuste lineal.",
        help_text=(
            "R² indica qué proporción de la variación del activo es explicada por el benchmark. "
            "Mientras más alto, más fuerte es la relación lineal activo-mercado."
        ),
    )

with c4:
    tarjeta_kpi(
        "Retorno esperado anual",
        _expected_return_text(expected_return_annual),
        subtexto="Retorno teórico compatible con el riesgo sistemático.",
        help_text=(
            "Es el retorno esperado bajo CAPM, calculado con la tasa libre de riesgo, "
            "la beta del activo y la prima de mercado."
        ),
    )

plot_card_footer(_capm_reading(payload))

seccion("Clasificación del activo")

render_info_card(
    "Clasificación obtenida",
    f"La clasificación obtenida es: {classification}. Esta etiqueta resume si el activo se comporta de forma más agresiva, defensiva o cercana al mercado.",
)
st.dataframe(table_df, use_container_width=True, hide_index=True)

seccion("Regresión CAPM")

plot_card_header(
    "Relación activo-mercado",
    (
        "La regresión CAPM compara los excesos de retorno del activo contra los excesos de retorno del benchmark. "
        "La pendiente de la recta corresponde a la beta."
    ),
    modo=modo,
    caption="Los puntos representan excesos de retorno del activo frente al benchmark; la recta resume la sensibilidad sistemática.",
)

r1, r2, r3 = st.columns(3)
with r1:
    show_points = st.checkbox("Puntos", value=True, key="capm_show_points")
with r2:
    show_line = st.checkbox("Recta CAPM", value=True, key="capm_show_line")
with r3:
    clean_view = st.checkbox("Vista limpia", value=False, key="capm_clean_view")

fig_reg = _build_regression_figure(
    points_df=points_df,
    modo=modo,
    show_points=show_points,
    show_line=show_line,
    clean_view=clean_view,
)

st.plotly_chart(fig_reg, use_container_width=True)

if points_df.empty:
    st.warning(
        "La API no devolvió observaciones utilizables para construir la nube de puntos de la regresión CAPM. "
        "Por eso la gráfica aparece vacía aunque sí exista beta."
    )
else:
    plot_card_footer(
    "La nube de puntos muestra la relación entre el activo y el benchmark. "
    "Una pendiente mayor implica beta más alta y, por tanto, mayor sensibilidad del activo frente al mercado."
    )
