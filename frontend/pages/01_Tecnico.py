from __future__ import annotations

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
    toolbar_label,
)
from ui.page_setup import setup_dashboard_page
from ui.plot_style import add_reference_line, style_plotly_figure


def _resolve_dates(horizonte: str, default_end: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
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
    else:
        start_date = end_date - pd.DateOffset(years=1)

    return pd.Timestamp(start_date).normalize(), end_date


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


def _fetch_technical_data(ticker: str, start: str, end: str) -> tuple[pd.DataFrame, str | None]:
    client = get_api_client()

    try:
        payload = client.get_technical_indicators(ticker=ticker, start=start, end=end)
    except ApiClientError as exc:
        return pd.DataFrame(), exc.message

    rows = payload.get("data", [])
    if not rows:
        return pd.DataFrame(), "La API no devolvió datos técnicos para el activo seleccionado."

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(), "La respuesta técnica llegó vacía."

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    numeric_cols = [
        "close",
        "sma_20",
        "ema_20",
        "rsi_14",
        "macd",
        "macd_signal",
        "macd_hist",
        "bb_mid",
        "bb_up",
        "bb_low",
        "stoch_k",
        "stoch_d",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df, None


def _latest_valid(series: pd.Series) -> float | None:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return None
    return float(clean.iloc[-1])


def _previous_valid(series: pd.Series) -> float | None:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if len(clean) < 2:
        return None
    return float(clean.iloc[-2])


def _format_delta(current: float | None, previous: float | None, as_pct: bool = True) -> str:
    if current is None or previous is None:
        return ""

    if previous == 0:
        return ""

    delta = (current / previous) - 1.0
    return f"{delta:+.2%}" if as_pct else f"{delta:+.4f}"


def _interpret_trend(close_now: float | None, sma_now: float | None, ema_now: float | None) -> str:
    if close_now is None or sma_now is None or ema_now is None:
        return "No hay suficiente información para interpretar la tendencia reciente."

    if close_now > sma_now and close_now > ema_now:
        return "El precio se ubica por encima de las medias móviles, compatible con una lectura alcista de corto plazo."
    if close_now < sma_now and close_now < ema_now:
        return "El precio se ubica por debajo de las medias móviles, compatible con una lectura de debilidad relativa."
    return "El precio está cerca de las medias móviles, lo que sugiere una zona de transición o consolidación."


def _interpret_rsi(rsi_now: float | None) -> str:
    if rsi_now is None:
        return "No fue posible construir una lectura actual del RSI."
    if rsi_now >= 70:
        return f"RSI en {rsi_now:.2f}: zona de sobrecompra relativa."
    if rsi_now <= 30:
        return f"RSI en {rsi_now:.2f}: zona de sobreventa relativa."
    return f"RSI en {rsi_now:.2f}: momentum intermedio sin señal extrema."


def _interpret_bollinger(close_now: float | None, bb_low: float | None, bb_up: float | None) -> str:
    if close_now is None or bb_low is None or bb_up is None:
        return "Observa la posición del precio frente a las bandas para identificar dispersión y posibles extremos."

    if close_now >= bb_up:
        return "El precio está tocando o superando la banda superior, señal de presión alcista o posible agotamiento."
    if close_now <= bb_low:
        return "El precio está tocando o perforando la banda inferior, señal de presión bajista o posible rebote técnico."
    return "El precio se mantiene dentro del canal de Bollinger, sin ruptura extrema reciente."


def _plot_price_ma(df: pd.DataFrame, modo: str) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["close"],
            mode="lines",
            name="Precio",
            line=dict(width=2.8),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["sma_20"],
            mode="lines",
            name="SMA 20",
            line=dict(width=2.1),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["ema_20"],
            mode="lines",
            name="EMA 20",
            line=dict(width=2.1),
        )
    )

    return style_plotly_figure(
        fig,
        modo=modo,
        title="Precio con medias móviles",
        xaxis_title="Fecha",
        yaxis_title="Precio",
        show_xgrid=False,
        show_ygrid=True,
    )


def _plot_bollinger(df: pd.DataFrame, modo: str) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df["date"], y=df["close"], mode="lines", name="Precio", line=dict(width=2.7)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["bb_mid"], mode="lines", name="Banda media", line=dict(width=1.9)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["bb_up"], mode="lines", name="Banda superior", line=dict(width=2.0, dash="dot")))
    fig.add_trace(go.Scatter(x=df["date"], y=df["bb_low"], mode="lines", name="Banda inferior", line=dict(width=2.0, dash="dot")))

    return style_plotly_figure(
        fig,
        modo=modo,
        title="Bandas de Bollinger",
        xaxis_title="Fecha",
        yaxis_title="Precio",
        show_xgrid=False,
        show_ygrid=True,
    )


def _plot_rsi(df: pd.DataFrame, modo: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["rsi_14"], mode="lines", name="RSI 14", line=dict(width=2.4)))
    add_reference_line(fig, 70)
    add_reference_line(fig, 30)
    fig.update_yaxes(range=[0, 100])

    return style_plotly_figure(
        fig,
        modo=modo,
        title="RSI",
        xaxis_title="Fecha",
        yaxis_title="RSI",
        show_xgrid=False,
        show_ygrid=True,
    )


def _plot_macd(df: pd.DataFrame, modo: str) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df["date"], y=df["macd"], mode="lines", name="MACD", line=dict(width=2.3)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["macd_signal"], mode="lines", name="Señal MACD", line=dict(width=2.1)))
    fig.add_trace(go.Bar(x=df["date"], y=df["macd_hist"], name="Histograma", opacity=0.78))

    return style_plotly_figure(
        fig,
        modo=modo,
        title="MACD",
        xaxis_title="Fecha",
        yaxis_title="Valor",
        show_xgrid=False,
        show_ygrid=True,
    )


def _plot_stochastic(df: pd.DataFrame, modo: str) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df["date"], y=df["stoch_k"], mode="lines", name="%K", line=dict(width=2.3)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["stoch_d"], mode="lines", name="%D", line=dict(width=2.1)))
    add_reference_line(fig, 80)
    add_reference_line(fig, 20)
    fig.update_yaxes(range=[0, 100])

    return style_plotly_figure(
        fig,
        modo=modo,
        title="Oscilador estocástico",
        xaxis_title="Fecha",
        yaxis_title="Nivel",
        show_xgrid=False,
        show_ygrid=True,
    )


assets, help_map, load_error = _fetch_assets_and_help()

modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros Técnicos",
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

with filtros_sidebar:
    selected_label = st.selectbox(
        "Activo",
        options=asset_labels,
        key="tec_asset_backend",
    )

    horizonte = st.selectbox(
        "Horizonte",
        ["1 mes", "Trimestre", "Semestre", "1 año", "3 años", "5 años"],
        index=3,
        key="tec_horizonte_backend",
    )

    show_price = st.checkbox("Mostrar precio", value=True, key="tec_show_price")
    show_sma = st.checkbox("Mostrar SMA 20", value=True, key="tec_show_sma")
    show_ema = st.checkbox("Mostrar EMA 20", value=True, key="tec_show_ema")
    show_bbands = st.checkbox("Mostrar Bollinger", value=True, key="tec_show_bbands")
    show_rsi = st.checkbox("Mostrar RSI", value=True, key="tec_show_rsi")
    show_macd = st.checkbox("Mostrar MACD", value=True, key="tec_show_macd")
    show_stoch = st.checkbox("Mostrar estocástico", value=True, key="tec_show_stoch")

selected_asset = asset_map[selected_label]
ticker = selected_asset["ticker"]
asset_name = selected_asset["name"]

default_end = pd.Timestamp.today().normalize()
start_date, end_date = _resolve_dates(horizonte, default_end)

df, technical_error = _fetch_technical_data(
    ticker=ticker,
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
)

header_dashboard(
    "Módulo 1 - Análisis técnico",
    "Explora tendencia, momentum y señales técnicas del activo seleccionado usando el backend FastAPI como fuente de indicadores",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo presenta una lectura ejecutiva del comportamiento técnico del activo seleccionado usando indicadores calculados desde backend."
    )
else:
    nota(
        "En modo estadístico se enfatiza la interpretación de tendencia, momentum y dispersión con base en indicadores técnicos calculados por la API."
    )

if technical_error:
    st.error(technical_error)
    st.stop()

close_now = _latest_valid(df["close"])
close_prev = _previous_valid(df["close"])
sma_now = _latest_valid(df["sma_20"])
ema_now = _latest_valid(df["ema_20"])
rsi_now = _latest_valid(df["rsi_14"])
macd_now = _latest_valid(df["macd"])
macd_signal_now = _latest_valid(df["macd_signal"])
bb_up_now = _latest_valid(df["bb_up"])
bb_low_now = _latest_valid(df["bb_low"])
stoch_k_now = _latest_valid(df["stoch_k"])

render_meta_row(
    [
        ("Activo", asset_name),
        ("Ticker", ticker),
        ("País", selected_asset["country"]),
        ("Horizonte", horizonte),
    ]
)

seccion("Resumen del módulo")

moving_averages_help = help_map.get("moving_averages", {})
rsi_help = help_map.get("rsi", {})
macd_help = help_map.get("macd", {})
boll_help = help_map.get("bollinger_bands", {})
stochastic_help = help_map.get("stochastic", {})

render_info_card(
    "Lectura técnica resumida",
    (
        f"{_interpret_trend(close_now, sma_now, ema_now)} "
        f"{_interpret_rsi(rsi_now)} "
        f"{_interpret_bollinger(close_now, bb_low_now, bb_up_now)} "
        f"Medias móviles: {moving_averages_help.get(modo.lower(), 'Ayuda no disponible')} "
        f"RSI: {rsi_help.get(modo.lower(), 'Ayuda no disponible')} "
        f"MACD: {macd_help.get(modo.lower(), 'Ayuda no disponible')} "
        f"Bollinger: {boll_help.get(modo.lower(), 'Ayuda no disponible')} "
        f"Estocástico: {stochastic_help.get(modo.lower(), 'Ayuda no disponible')}"
    ),
)

seccion("KPIs del activo")

c1, c2, c3, c4 = st.columns(4)

with c1:
    tarjeta_kpi(
        "Precio",
        f"{close_now:,.2f}" if close_now is not None else "N/D",
        delta=_format_delta(close_now, close_prev, as_pct=True),
        subtexto="Último precio disponible retornado por la API técnica.",
        help_text="Campo close entregado en el endpoint de indicadores técnicos.",
    )

with c2:
    tarjeta_kpi(
        "RSI 14",
        f"{rsi_now:.2f}" if rsi_now is not None else "N/D",
        subtexto="Momentum relativo del activo.",
        help_text=rsi_help.get(modo.lower(), "Oscilador técnico RSI."),
    )

with c3:
    tarjeta_kpi(
        "MACD neto",
        f"{(macd_now - macd_signal_now):.4f}" if macd_now is not None and macd_signal_now is not None else "N/D",
        subtexto="Diferencia entre MACD y línea de señal.",
        help_text=macd_help.get(modo.lower(), "Lectura de MACD."),
    )

with c4:
    tarjeta_kpi(
        "Stoch %K",
        f"{stoch_k_now:.2f}" if stoch_k_now is not None else "N/D",
        subtexto="Posición del cierre dentro del rango reciente.",
        help_text=stochastic_help.get(modo.lower(), "Lectura del estocástico."),
    )

plot_card_footer(
    f"Se cargaron {len(df)} observaciones técnicas para {asset_name} ({ticker}) entre {start_date.date()} y {end_date.date()}."
)

seccion("Visualizaciones técnicas")

if show_price:
    plot_card_header(
        "Precio y medias móviles",
        moving_averages_help.get(modo.lower(), "Precio, SMA 20 y EMA 20."),
        modo=modo,
        caption="Comparación entre precio de cierre y medias móviles calculadas por backend.",
    )

    toolbar_label("Series activas")
    render_chip_row(
        [
            "Precio" if show_price else "",
            "SMA 20" if show_sma else "",
            "EMA 20" if show_ema else "",
        ]
    )

    fig_price = _plot_price_ma(df, modo=modo)

    for trace in fig_price.data:
        name = str(getattr(trace, "name", "")).lower()
        if "precio" in name:
            trace.visible = True if show_price else "legendonly"
        elif "sma" in name:
            trace.visible = True if show_sma else "legendonly"
        elif "ema" in name:
            trace.visible = True if show_ema else "legendonly"

    st.plotly_chart(fig_price, use_container_width=True)
    plot_card_footer(_interpret_trend(close_now, sma_now, ema_now))

if show_bbands:
    plot_card_header(
        "Bandas de Bollinger",
        boll_help.get(modo.lower(), "Lectura de bandas de Bollinger."),
        modo=modo,
        caption="Dispersión del precio frente a la media móvil y bandas de desviación estándar.",
    )
    fig_boll = _plot_bollinger(df, modo=modo)
    st.plotly_chart(fig_boll, use_container_width=True)
    plot_card_footer(_interpret_bollinger(close_now, bb_low_now, bb_up_now))

g1, g2 = st.columns(2, gap="large")

with g1:
    if show_rsi:
        plot_card_header(
            "RSI",
            rsi_help.get(modo.lower(), "Lectura de RSI."),
            modo=modo,
            caption="Señal de momentum con líneas de referencia en 30 y 70.",
        )
        fig_rsi = _plot_rsi(df, modo=modo)
        st.plotly_chart(fig_rsi, use_container_width=True)
        plot_card_footer(_interpret_rsi(rsi_now))

with g2:
    if show_macd:
        plot_card_header(
            "MACD",
            macd_help.get(modo.lower(), "Lectura de MACD."),
            modo=modo,
            caption="Comparación entre línea MACD, línea de señal e histograma.",
        )
        fig_macd = _plot_macd(df, modo=modo)
        st.plotly_chart(fig_macd, use_container_width=True)
        plot_card_footer("Observa cruces y cambios en el histograma para evaluar aceleración o pérdida de momentum.")

if show_stoch:
    plot_card_header(
        "Oscilador estocástico",
        stochastic_help.get(modo.lower(), "Lectura del oscilador estocástico."),
        modo=modo,
        caption="Posiciona el cierre reciente dentro del rango móvil del activo.",
    )
    fig_stoch = _plot_stochastic(df, modo=modo)
    st.plotly_chart(fig_stoch, use_container_width=True)
    plot_card_footer("Usa %K y %D para identificar zonas extremas y posibles cambios de dirección de corto plazo.")