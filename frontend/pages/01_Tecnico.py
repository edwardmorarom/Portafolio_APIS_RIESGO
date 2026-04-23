from __future__ import annotations

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
    toolbar_label,
)
from ui.page_setup import setup_dashboard_page
from ui.plot_style import add_reference_line, style_plotly_figure


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


def _fetch_prices(ticker: str, start: str, end: str) -> tuple[pd.DataFrame, str | None]:
    client = get_api_client()

    try:
        payload = client.get_prices(ticker=ticker, start=start, end=end)
    except ApiClientError as exc:
        return pd.DataFrame(), exc.message

    rows = payload.get("data", [])
    if not rows:
        return pd.DataFrame(), "La API no devolvió precios para el activo seleccionado."

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(), "La respuesta de precios llegó vacía."

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    numeric_cols = ["open", "high", "low", "close", "adj_close", "volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df, None


def _build_technical_view(
    prices_df: pd.DataFrame,
    sma_window: int,
    ema_window: int,
    rsi_window: int,
    boll_window: int,
    stoch_window: int,
) -> pd.DataFrame:
    df = prices_df.copy()

    close = pd.to_numeric(df["close"], errors="coerce")
    high = pd.to_numeric(df["high"], errors="coerce")
    low = pd.to_numeric(df["low"], errors="coerce")

    df[f"sma_{sma_window}"] = close.rolling(sma_window).mean()
    df[f"ema_{ema_window}"] = close.ewm(span=ema_window, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / rsi_window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / rsi_window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df[f"rsi_{rsi_window}"] = 100 - (100 / (1 + rs))

    bb_mid = close.rolling(boll_window).mean()
    bb_std = close.rolling(boll_window).std(ddof=1)
    df[f"bb_mid_{boll_window}"] = bb_mid
    df[f"bb_up_{boll_window}"] = bb_mid + 2.0 * bb_std
    df[f"bb_low_{boll_window}"] = bb_mid - 2.0 * bb_std

    low_n = low.rolling(stoch_window).min()
    high_n = high.rolling(stoch_window).max()
    denom = (high_n - low_n).replace(0, np.nan)
    df[f"stoch_k_{stoch_window}"] = 100 * (close - low_n) / denom
    df[f"stoch_d_{stoch_window}"] = df[f"stoch_k_{stoch_window}"].rolling(3).mean()

    ema_fast = close.ewm(span=12, adjust=False).mean()
    ema_slow = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    return df.replace([np.inf, -np.inf], np.nan)


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
    if current is None or previous is None or previous == 0:
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
    return f"RSI en {rsi_now:.2f}: el momentum es intermedio y no muestra una señal extrema."


def _interpret_bollinger(close_now: float | None, bb_low: float | None, bb_up: float | None) -> str:
    if close_now is None or bb_low is None or bb_up is None:
        return "Observa la posición del precio frente a las bandas para identificar episodios de alta o baja dispersión."
    if close_now >= bb_up:
        return "El precio está tocando o superando la banda superior, lo que puede asociarse con presión alcista o agotamiento."
    if close_now <= bb_low:
        return "El precio está tocando o perforando la banda inferior, lo que puede asociarse con presión bajista o posible rebote."
    return "Observa la posición del precio frente a las bandas para identificar episodios de alta o baja dispersión."


def _plot_price_ma(df: pd.DataFrame, modo: str, sma_window: int, ema_window: int) -> go.Figure:
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
            y=df[f"sma_{sma_window}"],
            mode="lines",
            name=f"SMA {sma_window}",
            line=dict(width=2.1),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df[f"ema_{ema_window}"],
            mode="lines",
            name=f"EMA {ema_window}",
            line=dict(width=2.1),
        )
    )

    return style_plotly_figure(
        fig,
        modo=modo,
        title="Precio y medias móviles",
        xaxis_title="Fecha",
        yaxis_title="Precio",
        show_xgrid=False,
        show_ygrid=True,
    )


def _plot_rsi(df: pd.DataFrame, modo: str, rsi_window: int, show_levels: bool) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df[f"rsi_{rsi_window}"],
            mode="lines",
            name="Línea RSI",
            line=dict(width=2.3, color="#1E3A8A"),
        )
    )

    if show_levels:
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


def _plot_bollinger(
    df: pd.DataFrame,
    modo: str,
    boll_window: int,
    show_price: bool,
    show_mid: bool,
    show_up: bool,
    show_low: bool,
) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["close"],
            mode="lines",
            name="Precio",
            line=dict(width=2.5, color="#1E3A8A"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df[f"bb_mid_{boll_window}"],
            mode="lines",
            name="Media",
            line=dict(width=1.9, color="#8B5CF6"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df[f"bb_up_{boll_window}"],
            mode="lines",
            name="Banda sup.",
            line=dict(width=2.0, dash="dot", color="#10B981"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df[f"bb_low_{boll_window}"],
            mode="lines",
            name="Banda inf.",
            line=dict(width=2.0, dash="dot", color="#EF4444"),
        )
    )

    for trace in fig.data:
        name = str(getattr(trace, "name", "")).lower()
        if "precio" in name:
            trace.visible = True if show_price else "legendonly"
        elif "media" in name:
            trace.visible = True if show_mid else "legendonly"
        elif "sup" in name:
            trace.visible = True if show_up else "legendonly"
        elif "inf" in name:
            trace.visible = True if show_low else "legendonly"

    return style_plotly_figure(
        fig,
        modo=modo,
        title="Bandas de Bollinger",
        xaxis_title="Fecha",
        yaxis_title="Precio",
        show_xgrid=False,
        show_ygrid=True,
    )


assets, help_map, load_error = _fetch_assets_and_help()

modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros Técnicos Avanzados",
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
        key="tec_asset_backend",
        help="Selecciona el activo que quieres analizar técnicamente.",
    )

    horizonte = st.selectbox(
        "Horizonte de análisis",
        ["1 mes", "Trimestre", "Semestre", "1 año", "3 años", "5 años", "Personalizado"],
        index=3,
        key="tec_horizonte_backend",
        help="Define la ventana histórica a consultar desde backend.",
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
                key="tec_custom_start",
            )
        with c2:
            custom_end = st.date_input(
                "Fecha final",
                value=today.date(),
                max_value=today.date(),
                key="tec_custom_end",
            )

    sma_window = st.slider(
        "Ventana SMA",
        min_value=5,
        max_value=60,
        value=20,
        step=1,
        key="tec_sma_window",
        help="La SMA suaviza el precio con un promedio simple. Ventanas más grandes reducen ruido, pero reaccionan más lento.",
    )

    ema_window = st.slider(
        "Ventana EMA",
        min_value=5,
        max_value=60,
        value=20,
        step=1,
        key="tec_ema_window",
        help="La EMA da más peso a datos recientes. Reacciona más rápido que la SMA.",
    )

    rsi_window = st.slider(
        "Ventana RSI",
        min_value=5,
        max_value=30,
        value=14,
        step=1,
        key="tec_rsi_window",
        help="Controla la sensibilidad del RSI.",
    )

    boll_window = st.slider(
        "Bollinger",
        min_value=10,
        max_value=60,
        value=20,
        step=1,
        key="tec_boll_window",
        help="Ventana de media y desviación usada para las bandas.",
    )

    stoch_window = st.slider(
        "Estocástico",
        min_value=5,
        max_value=30,
        value=14,
        step=1,
        key="tec_stoch_window",
        help="Ventana usada para ubicar el cierre en su rango reciente.",
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

prices_df, technical_error = _fetch_prices(
    ticker=ticker,
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
)

header_dashboard(
    "Módulo 1 - Análisis técnico",
    "Explora tendencia, momentum y señales técnicas del activo seleccionado usando precios del backend FastAPI",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo presenta una lectura ejecutiva del comportamiento técnico del activo seleccionado."
    )
else:
    nota(
        "En modo estadístico se enfatiza una lectura más técnica: sensibilidad de ventanas, momentum, dispersión y apoyo visual para analizar el activo."
    )

if technical_error:
    st.error(technical_error)
    st.stop()

df = _build_technical_view(
    prices_df=prices_df,
    sma_window=sma_window,
    ema_window=ema_window,
    rsi_window=rsi_window,
    boll_window=boll_window,
    stoch_window=stoch_window,
)

close_now = _latest_valid(df["close"])
close_prev = _previous_valid(df["close"])
sma_now = _latest_valid(df[f"sma_{sma_window}"])
ema_now = _latest_valid(df[f"ema_{ema_window}"])
rsi_now = _latest_valid(df[f"rsi_{rsi_window}"])
bb_up_now = _latest_valid(df[f"bb_up_{boll_window}"])
bb_low_now = _latest_valid(df[f"bb_low_{boll_window}"])
stoch_k_now = _latest_valid(df[f"stoch_k_{stoch_window}"])

render_meta_row(
    [
        ("Activo", asset_name),
        ("Ticker", ticker),
        ("País", selected_asset["country"]),
        ("Horizonte", horizonte),
        ("SMA", str(sma_window)),
        ("EMA", str(ema_window)),
    ]
)

seccion("Resumen del módulo")

moving_averages_help = help_map.get("moving_averages", {})
rsi_help = help_map.get("rsi", {})
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
        subtexto="Último precio disponible retornado por la API de mercado.",
        help_text="Precio de cierre más reciente del activo en el rango consultado.",
    )

with c2:
    tarjeta_kpi(
        f"RSI {rsi_window}",
        f"{rsi_now:.2f}" if rsi_now is not None else "N/D",
        subtexto="Momentum relativo del activo.",
        help_text=rsi_help.get(modo.lower(), "Oscilador técnico RSI."),
    )

with c3:
    tarjeta_kpi(
        f"SMA {sma_window}",
        f"{sma_now:.2f}" if sma_now is not None else "N/D",
        subtexto=f"Media móvil simple de {sma_window} periodos.",
        help_text=moving_averages_help.get(modo.lower(), "Media móvil simple."),
    )

with c4:
    tarjeta_kpi(
        f"Stoch %K {stoch_window}",
        f"{stoch_k_now:.2f}" if stoch_k_now is not None else "N/D",
        subtexto=f"Posición del cierre en rango de {stoch_window} periodos.",
        help_text=stochastic_help.get(modo.lower(), "Lectura del estocástico."),
    )

plot_card_footer(
    f"Se cargaron {len(df)} observaciones para {asset_name} ({ticker}) entre {start_date.date()} y {end_date.date()}."
)

seccion("Visualizaciones técnicas")

plot_card_header(
    "Precio y medias móviles",
    moving_averages_help.get(modo.lower(), "Comparación entre precio, SMA y EMA."),
    modo=modo,
    caption="Compara la dirección del precio con las medias configuradas desde el panel lateral.",
)

toolbar_label("Capas del gráfico")
render_chip_row(
    [
        "Precio",
        f"SMA {sma_window}",
        f"EMA {ema_window}",
    ]
)

fig_price = _plot_price_ma(df, modo=modo, sma_window=sma_window, ema_window=ema_window)
st.plotly_chart(fig_price, use_container_width=True)
plot_card_footer(_interpret_trend(close_now, sma_now, ema_now))

g1, g2 = st.columns(2, gap="large")

with g1:
    plot_card_header(
        "RSI",
        rsi_help.get(modo.lower(), "Lectura de RSI."),
        modo=modo,
        caption="Controla si deseas una lectura más limpia del oscilador o conservar referencias visuales.",
    )

    toolbar_label("Capas del gráfico")
    r1, r2 = st.columns(2)
    with r1:
        rsi_line = st.checkbox("Línea RSI", value=True, key="tec_rsi_line")
    with r2:
        rsi_levels = st.checkbox("Niveles 30/70", value=True, key="tec_rsi_levels")

    fig_rsi = _plot_rsi(df, modo=modo, rsi_window=rsi_window, show_levels=rsi_levels)
    if not rsi_line:
        for trace in fig_rsi.data:
            trace.visible = "legendonly"

    st.plotly_chart(fig_rsi, use_container_width=True)
    plot_card_footer(_interpret_rsi(rsi_now))

with g2:
    plot_card_header(
        "Bandas de Bollinger",
        boll_help.get(modo.lower(), "Lectura de bandas de Bollinger."),
        modo=modo,
        caption="Puedes decidir si observar solo el precio o comparar contra la media y las bandas.",
    )

    toolbar_label("Capas del gráfico")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        show_boll_price = st.checkbox("Precio", value=True, key="tec_boll_price")
    with b2:
        show_boll_mid = st.checkbox("Media", value=True, key="tec_boll_mid")
    with b3:
        show_boll_up = st.checkbox("Banda sup.", value=True, key="tec_boll_up")
    with b4:
        show_boll_low = st.checkbox("Banda inf.", value=True, key="tec_boll_low")

    fig_boll = _plot_bollinger(
        df=df,
        modo=modo,
        boll_window=boll_window,
        show_price=show_boll_price,
        show_mid=show_boll_mid,
        show_up=show_boll_up,
        show_low=show_boll_low,
    )
    st.plotly_chart(fig_boll, use_container_width=True)
    plot_card_footer(_interpret_bollinger(close_now, bb_low_now, bb_up_now))

if modo == "Estadístico":
    seccion("Datos recientes")

    recent_cols = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
        f"sma_{sma_window}",
        f"ema_{ema_window}",
        f"rsi_{rsi_window}",
        "macd",
        "macd_signal",
        "macd_hist",
        f"bb_mid_{boll_window}",
        f"bb_up_{boll_window}",
        f"bb_low_{boll_window}",
        f"stoch_k_{stoch_window}",
        f"stoch_d_{stoch_window}",
    ]

    recent_df = df[recent_cols].copy().tail(10).sort_values("date", ascending=False)
    recent_df["date"] = recent_df["date"].dt.strftime("%Y-%m-%d")

    with st.expander("Ver tabla", expanded=False):
        st.dataframe(recent_df, use_container_width=True)