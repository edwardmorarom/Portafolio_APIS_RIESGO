from __future__ import annotations

import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_chip_row, render_info_card, render_meta_row
from ui.dashboard_ui import (
    header_dashboard,
    nota,
    plot_card_footer,
    plot_card_header,
    seccion,
    tarjeta_kpi,
    titulo_con_ayuda,
)
from ui.page_setup import setup_dashboard_page
from ui.plot_style import style_plotly_figure


def _fetch_assets_and_help() -> tuple[list[dict], dict[str, dict], str | None]:
    client = get_api_client()

    try:
        assets_payload = client.get_assets()
        assets = assets_payload.get("assets", [])
    except ApiClientError as exc:
        return [], {}, f"No fue posible cargar activos desde backend: {exc.message}"

    try:
        help_payload = client.get_help_catalog()
        help_map = {item["key"]: item for item in help_payload.get("items", [])}
    except ApiClientError:
        help_map = {}

    return assets, help_map, None


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


def _fetch_returns_stats(
    ticker: str,
    start: str,
    end: str,
    return_type: str,
    mode: str,
) -> tuple[dict, str | None]:
    client = get_api_client()

    try:
        payload = client.get_returns_stats(
            ticker=ticker,
            start=start,
            end=end,
            return_type=return_type,
            mode=mode,
        )
        return payload, None
    except ApiClientError as exc:
        return {}, exc.message


def _fetch_raw_returns(
    ticker: str,
    start: str,
    end: str,
) -> tuple[pd.DataFrame, str | None]:
    client = get_api_client()

    try:
        payload = client.get_returns(ticker=ticker, start=start, end=end)
    except ApiClientError as exc:
        return pd.DataFrame(), exc.message

    rows = payload.get("data", [])
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(), "No fue posible cargar los rendimientos recientes."

    df["date"] = pd.to_datetime(df["date"])
    df["simple_return"] = pd.to_numeric(df["simple_return"], errors="coerce")
    df["log_return"] = pd.to_numeric(df["log_return"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)
    return df, None


def _normal_pdf(x: np.ndarray, mean: float, std: float) -> np.ndarray:
    if std is None or std <= 0 or not np.isfinite(std):
        return np.zeros_like(x)
    coef = 1.0 / (std * math.sqrt(2.0 * math.pi))
    return coef * np.exp(-0.5 * ((x - mean) / std) ** 2)


def _build_histogram_figure(
    returns_df: pd.DataFrame,
    return_type: str,
    modo: str,
    show_hist: bool,
    show_normal: bool,
) -> go.Figure:
    series = returns_df[f"{return_type}_return"].dropna()
    fig = go.Figure()

    if not series.empty:
        fig.add_trace(
            go.Histogram(
                x=series,
                histnorm="probability density",
                name="Histograma",
                opacity=0.62,
                nbinsx=30,
            )
        )

        x_grid = np.linspace(series.min(), series.max(), 200)
        y_grid = _normal_pdf(x_grid, float(series.mean()), float(series.std(ddof=1)))
        fig.add_trace(
            go.Scatter(
                x=x_grid,
                y=y_grid,
                mode="lines",
                name="Normal teórica",
                line=dict(width=2.4),
            )
        )

    for trace in fig.data:
        name = str(getattr(trace, "name", "")).lower()
        if "histograma" in name:
            trace.visible = True if show_hist else "legendonly"
        elif "normal" in name:
            trace.visible = True if show_normal else "legendonly"

    return style_plotly_figure(
        fig,
        modo=modo,
        title="Histograma con curva normal",
        xaxis_title="Rendimiento",
        yaxis_title="Densidad",
        show_xgrid=True,
        show_ygrid=True,
    )


def _build_boxplot_figure(
    returns_df: pd.DataFrame,
    return_type: str,
    modo: str,
    horizontal: bool,
) -> go.Figure:
    series = returns_df[f"{return_type}_return"].dropna()
    fig = go.Figure()

    if horizontal:
        fig.add_trace(
            go.Box(
                x=series,
                name="Rendimientos",
                boxpoints="outliers",
                orientation="h",
            )
        )
    else:
        fig.add_trace(
            go.Box(
                y=series,
                name="Rendimientos",
                boxpoints="outliers",
            )
        )

    return style_plotly_figure(
        fig,
        modo=modo,
        title="Boxplot de rendimientos",
        xaxis_title="Rendimientos" if horizontal else "",
        yaxis_title="" if horizontal else "Rendimiento",
        show_xgrid=True,
        show_ygrid=True,
    )


def _render_test_card(title: str, metric_label: str, metric_value, conclusion: str, note: str = ""):
    value_text = "N/D" if metric_value is None else f"{float(metric_value):.8f}"

    if "no se rechaza" in conclusion.lower():
        short_conclusion = "No se rechaza normalidad"
    else:
        short_conclusion = "Se rechaza normalidad"

    st.markdown(
        f"""
        <div class="ui-test-card">
            <div class="ui-test-head">
                <div class="ui-test-title">{title}</div>
                <span class="ui-help" title="{conclusion}">?</span>
            </div>
            <div class="ui-test-value">{metric_label}: {value_text}</div>
            <div class="ui-test-conclusion">{short_conclusion}</div>
            {'<div class="ui-test-note">' + note + '</div>' if note else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )

def _help_badge(text: str):
    st.markdown(
        f"""
        <span class="ui-help" title="{text}">?</span>
        """,
        unsafe_allow_html=True,
    )

assets, help_map, load_error = _fetch_assets_and_help()

modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros de Rendimientos",
    filtros_expanded=False,
)

if load_error:
    st.error(load_error)
    st.stop()

asset_labels = []
asset_map: dict[str, dict] = {}
for asset in assets:
    label = f"{asset['name']} · {asset['ticker']} · {asset['country']}"
    asset_labels.append(label)
    asset_map[label] = asset

today = pd.Timestamp.today().normalize()

with filtros_sidebar:
    selected_label = st.selectbox(
        "Activo",
        options=asset_labels,
        key="ret_asset_backend",
        help="Selecciona el activo para analizar la distribución de sus rendimientos.",
    )

    horizonte = st.selectbox(
        "Horizonte de análisis",
        ["1 mes", "Trimestre", "Semestre", "1 año", "3 años", "5 años", "Personalizado"],
        index=3,
        key="ret_horizonte_backend",
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
                key="ret_custom_start",
            )
        with c2:
            custom_end = st.date_input(
                "Fecha final",
                value=today.date(),
                max_value=today.date(),
                key="ret_custom_end",
            )

    return_type = st.radio(
        "Tipo de rendimiento",
        ["log", "simple"],
        index=0,
        key="ret_return_type",
        horizontal=True,
        help="Selecciona si quieres analizar retornos logarítmicos o simples.",
    )

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

payload, returns_error = _fetch_returns_stats(
    ticker=ticker,
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
    return_type=return_type,
    mode=modo.lower(),
)

returns_df, raw_returns_error = _fetch_raw_returns(
    ticker=ticker,
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
)

header_dashboard(
    "Módulo 2 - Rendimientos",
    "Analiza la distribución, dispersión y evidencia de normalidad de los rendimientos del activo seleccionado",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo permite identificar si los rendimientos lucen estables, dispersos o alejados de una forma aproximadamente normal."
    )
else:
    nota(
        "En modo estadístico se enfatiza la lectura distribucional: densidad, colas, asimetría, outliers y evidencia de rechazo o no rechazo de normalidad."
    )

if returns_error:
    st.error(returns_error)
    st.stop()

if raw_returns_error:
    st.error(raw_returns_error)
    st.stop()

observations = payload.get("observations")
mean_ = payload.get("mean")
std_ = payload.get("std")
skewness = payload.get("skewness")
kurtosis = payload.get("kurtosis")
min_return = payload.get("min_return")
max_return = payload.get("max_return")

shapiro = payload.get("shapiro_wilk", {})
jb = payload.get("jarque_bera", {})
ad = payload.get("anderson_darling", {})

render_meta_row(
    [
        ("Activo", asset_name),
        ("Ticker", ticker),
        ("País", selected_asset["country"]),
        ("Horizonte", horizonte),
        ("Retorno", return_type),
    ]
)

seccion("KPIs del activo")

c1, c2, c3, c4 = st.columns(4)

with c1:
    tarjeta_kpi(
        "Observaciones",
        str(observations) if observations is not None else "N/D",
        subtexto="Cantidad de rendimientos usados en el análisis.",
        help_text="Número de observaciones efectivas entregadas por el endpoint estadístico.",
    )

with c2:
    tarjeta_kpi(
        "Media",
        f"{mean_:.6f}" if mean_ is not None else "N/D",
        subtexto="Promedio de los rendimientos observados.",
        help_text="Media muestral de la serie de rendimientos.",
    )

with c3:
    tarjeta_kpi(
        "Volatilidad",
        f"{std_:.6f}" if std_ is not None else "N/D",
        subtexto="Desviación estándar muestral.",
        help_text="Dispersión de los rendimientos frente a su media.",
    )

with c4:
    tarjeta_kpi(
        "Asimetría",
        f"{skewness:.4f}" if skewness is not None else "N/D",
        subtexto="Sesgo de la distribución.",
        help_text="Mide si la distribución se inclina hacia la izquierda o la derecha.",
    )

c5, c6, c7, c8 = st.columns(4)

with c5:
    tarjeta_kpi(
        "Curtosis",
        f"{kurtosis:.4f}" if kurtosis is not None else "N/D",
        subtexto="Peso de colas y concentración relativa.",
        help_text="Curtosis de la distribución de rendimientos.",
    )

with c6:
    tarjeta_kpi(
        "Mínimo",
        f"{min_return:.6f}" if min_return is not None else "N/D",
        subtexto="Peor rendimiento observado.",
        help_text="Valor mínimo de la serie de rendimientos.",
    )

with c7:
    tarjeta_kpi(
        "Máximo",
        f"{max_return:.6f}" if max_return is not None else "N/D",
        subtexto="Mejor rendimiento observado.",
        help_text="Valor máximo de la serie de rendimientos.",
    )

with c8:
    tarjeta_kpi(
        "Tipo",
        return_type.upper(),
        subtexto="Retornos usados en los gráficos y métricas.",
        help_text="Selección actual entre rendimientos simples y logarítmicos.",
    )

seccion("Últimos rendimientos")

c_help_1, c_help_2 = st.columns([12, 1])
with c_help_1:
    st.markdown("**Tabla de retornos recientes**")
with c_help_2:
    _help_badge(
        "Retorno simple: variación porcentual entre un periodo y el siguiente. "
        "Log-retorno: logaritmo natural de (P_t / P_{t-1}); se usa mucho en finanzas "
        "porque facilita agregación temporal y análisis estadístico."
    )

recent_df = returns_df[["date", "simple_return", "log_return"]].copy().tail(10).sort_values("date", ascending=False)
recent_df["date"] = recent_df["date"].dt.strftime("%Y-%m-%d")
recent_df = recent_df.rename(
    columns={
        "date": "Fecha",
        "simple_return": "Retorno simple",
        "log_return": "Log-retorno",
    }
)
st.dataframe(recent_df, width="stretch")

seccion("Pruebas de normalidad")

n1, n2, n3 = st.columns(3)

with n1:
    _render_test_card(
        "Shapiro-Wilk",
        "p-value",
        shapiro.get("p_value"),
        shapiro.get("conclusion", "Sin conclusión disponible."),
        note="No se recomienda este test para series financieras largas o con colas marcadas.",
    )

with n2:
    _render_test_card(
        "Jarque-Bera",
        "p-value",
        jb.get("p_value"),
        jb.get("conclusion", "Sin conclusión disponible."),
    )

with n3:
    ad_note = ""
    if observations is not None and observations > 500:
        ad_note = "Cuando la muestra es mayor a 500 observaciones, esta prueba no es la más recomendable como referencia principal."

    _render_test_card(
        "Anderson-Darling",
        "estadístico",
        ad.get("statistic"),
        ad.get("conclusion", "Sin conclusión disponible."),
        note=ad_note,
    )

seccion("Visualizaciones")

g1, g2 = st.columns(2, gap="large")

with g1:
    plot_card_header(
        "Histograma con referencia normal",
        help_map.get("histogram_normal", {}).get(modo.lower(), "Compara la distribución empírica con una forma normal teórica."),
        modo=modo,
        caption="Activa o desactiva elementos para simplificar o ampliar la lectura visual.",
    )

    st.markdown("**CAPAS DEL GRÁFICO**")
    h1, h2 = st.columns(2)
    with h1:
        show_hist = st.checkbox("Histograma", value=True, key="ret_show_hist")
    with h2:
        show_normal = st.checkbox("Curva normal", value=True, key="ret_show_normal")

    fig_hist = _build_histogram_figure(
        returns_df=returns_df,
        return_type=return_type,
        modo=modo,
        show_hist=show_hist,
        show_normal=show_normal,
    )
    st.plotly_chart(fig_hist, width="stretch")
    plot_card_footer("Observa si la distribución se concentra cerca de cero o si presenta colas amplias, lo que puede indicar episodios de variación más fuerte.")

with g2:
    plot_card_header(
        "Boxplot de rendimientos",
        help_map.get("boxplot", {}).get(modo.lower(), "Resume mediana, dispersión y valores extremos."),
        modo=modo,
        caption="Útil para identificar rápidamente dispersión y extremos.",
    )

    st.markdown("**OPCIONES DEL GRÁFICO**")
    horizontal_box = st.checkbox("Orientación horizontal", value=False, key="ret_box_horizontal")

    fig_box = _build_boxplot_figure(
        returns_df=returns_df,
        return_type=return_type,
        modo=modo,
        horizontal=horizontal_box,
    )
    st.plotly_chart(fig_box, width="stretch")
    plot_card_footer("El boxplot resume mediana, dispersión y valores atípicos. Una caja amplia o muchos outliers suele asociarse con mayor inestabilidad en los rendimientos.")