from __future__ import annotations

import pandas as pd
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_ui import (
    header_dashboard,
    nota,
    plot_card_footer,
    seccion,
    tarjeta_kpi,
)
from ui.page_setup import setup_dashboard_page


RSI_DEFAULT_OVERBOUGHT = 70
RSI_DEFAULT_OVERSOLD = 30
STOCH_DEFAULT_OVERBOUGHT = 80
STOCH_DEFAULT_OVERSOLD = 20


RULES = [
    {
        "key": "macd",
        "title": "Cruce del MACD",
        "subtitle": "Línea MACD cruzando señal",
        "keywords": ["macd", "signal line", "cruce macd", "macd cross"],
    },
    {
        "key": "rsi",
        "title": "RSI en zonas extremas",
        "subtitle": "RSI mayor a 70 o menor a 30",
        "keywords": ["rsi", "sobrecompra", "sobreventa", "overbought", "oversold"],
    },
    {
        "key": "bollinger",
        "title": "Bandas de Bollinger",
        "subtitle": "Precio tocando banda superior o inferior",
        "keywords": ["bollinger", "bb", "banda superior", "banda inferior", "upper band", "lower band"],
    },
    {
        "key": "moving_average",
        "title": "Cruce de medias móviles",
        "subtitle": "Golden cross / Death cross",
        "keywords": ["golden cross", "death cross", "moving average", "media móvil", "sma", "ema", "cruce de medias"],
    },
    {
        "key": "stochastic",
        "title": "Oscilador Estocástico",
        "subtitle": "%K cruzando %D en zonas extremas",
        "keywords": ["stoch", "stochastic", "%k", "%d", "estocástico"],
    },
]


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


def _fetch_alerts(
    ticker: str,
    start: str,
    end: str,
    rsi_overbought: float,
    rsi_oversold: float,
    stoch_overbought: float,
    stoch_oversold: float,
) -> tuple[dict, str | None]:
    client = get_api_client()

    try:
        payload = client.get_alerts(
            ticker=ticker,
            start=start,
            end=end,
            rsi_overbought=rsi_overbought,
            rsi_oversold=rsi_oversold,
            stoch_overbought=stoch_overbought,
            stoch_oversold=stoch_oversold,
        )
        if payload is None:
            return {}, "El endpoint de señales respondió vacío."
        if not isinstance(payload, dict):
            return {}, f"Respuesta de señales no válida: {type(payload).__name__}"
        return payload, None
    except ApiClientError as exc:
        return {}, exc.message
    except Exception as exc:
        return {}, f"Error inesperado consultando señales: {exc}"


def _pick_value(payload: dict | None, *keys):
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _extract_alerts_df(payload: dict) -> pd.DataFrame:
    for key in ["alerts", "signals", "events", "data", "rows"]:
        val = payload.get(key)
        if isinstance(val, list) and val:
            df = pd.DataFrame(val)
            if not df.empty:
                return df
    return pd.DataFrame()


def _normalize_alerts_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Fecha", "Señal", "Indicador", "Valor", "Descripción", "texto_busqueda"])

    lowered = {c.lower(): c for c in df.columns}

    def pick(*names):
        for n in names:
            if n in lowered:
                return lowered[n]
        return None

    date_col = pick("date", "fecha", "timestamp", "datetime")
    signal_col = pick("signal", "type", "tipo", "alert", "alert_type")
    value_col = pick("value", "valor", "indicator_value", "signal_value")
    indicator_col = pick("indicator", "indicador", "source")
    message_col = pick("message", "mensaje", "description", "descripcion", "detail", "detalle")

    out = pd.DataFrame()
    out["Fecha"] = pd.to_datetime(df[date_col], errors="coerce") if date_col else pd.NaT
    out["Señal"] = df[signal_col].astype(str) if signal_col else "N/D"
    out["Indicador"] = df[indicator_col].astype(str) if indicator_col else "N/D"
    out["Valor"] = pd.to_numeric(df[value_col], errors="coerce") if value_col else None
    out["Descripción"] = df[message_col].astype(str) if message_col else ""

    out["texto_busqueda"] = (
        out["Señal"].astype(str).fillna("")
        + " "
        + out["Indicador"].astype(str).fillna("")
        + " "
        + out["Descripción"].astype(str).fillna("")
    ).str.lower()

    out = out.sort_values("Fecha", ascending=False)
    return out.reset_index(drop=True)


def _classify_status(text: str) -> tuple[str, str]:
    t = str(text).lower()

    if any(x in t for x in ["compra", "buy", "sobreventa", "oversold", "golden cross", "rebote"]):
        return "COMPRA", "#15803d"

    if any(x in t for x in ["venta", "sell", "sobrecompra", "overbought", "death cross", "agotamiento"]):
        return "VENTA", "#b91c1c"

    if any(x in t for x in ["alerta", "warning", "precauc", "watch"]):
        return "ALERTA", "#b45309"

    return "SIN SEÑAL", "#475569"


def _latest_for_rule(alerts_df: pd.DataFrame, rule: dict) -> dict | None:
    if alerts_df.empty:
        return None

    mask = pd.Series(False, index=alerts_df.index)
    for kw in rule["keywords"]:
        mask = mask | alerts_df["texto_busqueda"].str.contains(kw, case=False, na=False)

    filtered = alerts_df[mask].copy()
    if filtered.empty:
        return None

    row = filtered.iloc[0]
    return {
        "fecha": row["Fecha"],
        "senal": row["Señal"],
        "indicador": row["Indicador"],
        "valor": row["Valor"],
        "descripcion": row["Descripción"],
    }


def _signal_summary(alerts_df: pd.DataFrame) -> dict[str, int]:
    if alerts_df.empty:
        return {"total": 0, "compra": 0, "venta": 0, "alerta": 0, "sin_clasificar": 0}

    compra = 0
    venta = 0
    alerta = 0
    sin_clasificar = 0

    for _, row in alerts_df.iterrows():
        status, _ = _classify_status(
            f"{row['Señal']} {row['Indicador']} {row['Descripción']}"
        )
        if status == "COMPRA":
            compra += 1
        elif status == "VENTA":
            venta += 1
        elif status == "ALERTA":
            alerta += 1
        else:
            sin_clasificar += 1

    return {
        "total": int(len(alerts_df)),
        "compra": compra,
        "venta": venta,
        "alerta": alerta,
        "sin_clasificar": sin_clasificar,
    }


def _latest_metrics(payload: dict, alerts_df: pd.DataFrame) -> tuple[float | None, float | None]:
    latest_rsi = _pick_value(payload, "latest_rsi", "rsi_latest", "rsi")
    latest_stoch = _pick_value(payload, "latest_stoch", "stoch_latest", "stochastic", "stoch_k")

    if latest_rsi is None and not alerts_df.empty:
        rsi_rows = alerts_df[alerts_df["texto_busqueda"].str.contains("rsi", na=False)]
        if not rsi_rows.empty:
            latest_rsi = rsi_rows.iloc[0]["Valor"]

    if latest_stoch is None and not alerts_df.empty:
        stoch_rows = alerts_df[alerts_df["texto_busqueda"].str.contains("stoch|estoc", regex=True, na=False)]
        if not stoch_rows.empty:
            latest_stoch = stoch_rows.iloc[0]["Valor"]

    return latest_rsi, latest_stoch


def _render_signal_card(rule: dict, latest_event: dict | None):
    if latest_event is None:
        status = "SIN SEÑAL"
        color = "#475569"
        fecha = "N/D"
        valor = "N/D"
        detalle = "No llegó una alerta explícita del backend para esta regla en el rango consultado."
    else:
        status, color = _classify_status(
            f"{latest_event['senal']} {latest_event['indicador']} {latest_event['descripcion']}"
        )
        fecha = (
            pd.to_datetime(latest_event["fecha"]).strftime("%Y-%m-%d")
            if pd.notna(latest_event["fecha"])
            else "N/D"
        )
        valor = "N/D" if pd.isna(latest_event["valor"]) else f"{float(latest_event['valor']):.2f}"
        detalle = latest_event["descripcion"] or str(latest_event["senal"])

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(180deg, #ffffff 0%, var(--panel-bg-2) 100%);
            border: 1px solid var(--border-soft);
            border-radius: 18px;
            box-shadow: var(--shadow-main);
            padding: 1rem 1rem 0.95rem 1rem;
            position: relative;
            overflow: hidden;
            min-height: 220px;
        ">
            <div style="
                position:absolute;
                left:0;
                top:0;
                width:100%;
                height:4px;
                background:{color};
            "></div>

            <div style="display:flex;align-items:center;justify-content:space-between;gap:0.7rem;margin-bottom:0.6rem;">
                <div style="font-size:1rem;font-weight:800;color:var(--text-main);">{rule["title"]}</div>
                <div style="
                    padding:0.30rem 0.65rem;
                    border-radius:999px;
                    background:{color}18;
                    color:{color};
                    border:1px solid {color}55;
                    font-size:0.78rem;
                    font-weight:900;
                ">
                    {status}
                </div>
            </div>

            <div style="font-size:0.90rem;font-weight:700;color:var(--text-soft);margin-bottom:0.45rem;">
                {rule["subtitle"]}
            </div>

            <div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:0.18rem;">
                <strong>Fecha:</strong> {fecha}
            </div>

            <div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:0.55rem;">
                <strong>Valor:</strong> {valor}
            </div>

            <div style="
                font-size:0.90rem;
                line-height:1.5;
                color:var(--text-soft);
                font-weight:600;
            ">
                {detalle}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _reading_text(summary: dict[str, int], latest_rsi: float | None, latest_stoch: float | None) -> str:
    rsi_text = f"{float(latest_rsi):.2f}" if latest_rsi is not None else "N/D"
    stoch_text = f"{float(latest_stoch):.2f}" if latest_stoch is not None else "N/D"

    return (
        f"Se identificaron {summary['total']} alertas en la ventana analizada: "
        f"{summary['compra']} de compra/sobreventa, {summary['venta']} de venta/sobrecompra, "
        f"{summary['alerta']} de precaución y {summary['sin_clasificar']} sin clasificar. "
        f"Los últimos niveles observados son RSI={rsi_text} y Estocástico={stoch_text}."
    )


assets, help_map, load_error = _fetch_assets_and_help()

modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros de Señales",
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
        key="signals_asset_backend",
        help="Selecciona el activo para consultar alertas técnicas desde backend.",
    )

    horizonte = st.selectbox(
        "Horizonte de análisis",
        ["1 mes", "Trimestre", "Semestre", "1 año", "3 años", "5 años", "Personalizado"],
        index=3,
        key="signals_horizonte_backend",
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
                key="signals_custom_start",
            )
        with c2:
            custom_end = st.date_input(
                "Fecha final",
                value=today.date(),
                max_value=today.date(),
                key="signals_custom_end",
            )

    rsi_overbought = st.number_input(
        "RSI sobrecompra",
        min_value=50.0,
        max_value=100.0,
        value=float(RSI_DEFAULT_OVERBOUGHT),
        step=1.0,
        key="signals_rsi_overbought",
    )
    rsi_oversold = st.number_input(
        "RSI sobreventa",
        min_value=0.0,
        max_value=50.0,
        value=float(RSI_DEFAULT_OVERSOLD),
        step=1.0,
        key="signals_rsi_oversold",
    )
    stoch_overbought = st.number_input(
        "Estocástico sobrecompra",
        min_value=50.0,
        max_value=100.0,
        value=float(STOCH_DEFAULT_OVERBOUGHT),
        step=1.0,
        key="signals_stoch_overbought",
    )
    stoch_oversold = st.number_input(
        "Estocástico sobreventa",
        min_value=0.0,
        max_value=50.0,
        value=float(STOCH_DEFAULT_OVERSOLD),
        step=1.0,
        key="signals_stoch_oversold",
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

payload, alerts_error = _fetch_alerts(
    ticker=ticker,
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
    rsi_overbought=rsi_overbought,
    rsi_oversold=rsi_oversold,
    stoch_overbought=stoch_overbought,
    stoch_oversold=stoch_oversold,
)

header_dashboard(
    "Módulo 7 - Señales",
    "Operacionaliza indicadores técnicos como señales de compra, venta o alerta por activo",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo organiza las alertas del backend como un panel tipo semáforo para resumir zonas de compra, venta o vigilancia técnica."
    )
else:
    nota(
        "En modo estadístico se enfatiza la trazabilidad de las reglas activas, la clasificación de eventos y el detalle de las alertas detectadas."
    )

if alerts_error:
    st.error(alerts_error)
    st.stop()

if not isinstance(payload, dict) or not payload:
    st.error("No se recibieron datos válidos del endpoint de señales.")
    st.stop()

alerts_df_raw = _extract_alerts_df(payload)
alerts_df = _normalize_alerts_df(alerts_df_raw)
summary = _signal_summary(alerts_df)
latest_rsi, latest_stoch = _latest_metrics(payload, alerts_df)

render_meta_row(
    [
        ("Activo", asset_name),
        ("Ticker", ticker),
        ("Horizonte", horizonte),
        ("RSI", f"{int(rsi_oversold)}/{int(rsi_overbought)}"),
        ("Estocástico", f"{int(stoch_oversold)}/{int(stoch_overbought)}"),
    ]
)

seccion("Panel de alertas por criterio")

c1, c2 = st.columns(2, gap="large")
with c1:
    _render_signal_card(RULES[0], _latest_for_rule(alerts_df, RULES[0]))
with c2:
    _render_signal_card(RULES[1], _latest_for_rule(alerts_df, RULES[1]))

c3, c4 = st.columns(2, gap="large")
with c3:
    _render_signal_card(RULES[2], _latest_for_rule(alerts_df, RULES[2]))
with c4:
    _render_signal_card(RULES[3], _latest_for_rule(alerts_df, RULES[3]))

c5, c6 = st.columns([1, 1], gap="large")
with c5:
    _render_signal_card(RULES[4], _latest_for_rule(alerts_df, RULES[4]))
with c6:
    tarjeta_kpi(
        "Resumen automático",
        str(summary["total"]),
        subtexto="Total de alertas detectadas por el backend en el rango consultado.",
        help_text="Incluye señales clasificadas como compra, venta, alerta o sin clasificar.",
    )

plot_card_footer(_reading_text(summary, latest_rsi, latest_stoch))

seccion("KPIs del módulo")

k1, k2, k3, k4 = st.columns(4)

with k1:
    tarjeta_kpi(
        "Compra / sobreventa",
        str(summary["compra"]),
        subtexto="Eventos con lectura potencialmente alcista.",
        help_text="Incluye compra, oversold o sobreventa.",
    )
with k2:
    tarjeta_kpi(
        "Venta / sobrecompra",
        str(summary["venta"]),
        subtexto="Eventos con lectura potencialmente bajista.",
        help_text="Incluye venta, overbought o sobrecompra.",
    )
with k3:
    tarjeta_kpi(
        "Alerta",
        str(summary["alerta"]),
        subtexto="Eventos que sugieren vigilancia adicional.",
        help_text="Señales marcadas como alerta o precaución.",
    )
with k4:
    tarjeta_kpi(
        "Sin clasificar",
        str(summary["sin_clasificar"]),
        subtexto="Eventos no mapeados a compra/venta/alerta.",
        help_text="Ayuda a detectar mensajes del backend que necesitan mejor clasificación visual.",
    )

seccion("Presentación")

render_info_card(
    "Criterios operativos",
    "El sistema resume señales de MACD, RSI, Bollinger, cruces de medias y estocástico en tarjetas tipo semáforo por activo. Los umbrales permanecen configurables desde el panel lateral y la lectura se acompaña con texto interpretativo automático.",
)

seccion("Detalle de alertas")

if alerts_df.empty:
    st.info("No hay alertas para mostrar en este rango.")
else:
    df_show = alerts_df.copy()
    if "Fecha" in df_show.columns:
        df_show["Fecha"] = pd.to_datetime(df_show["Fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
    df_show = df_show.drop(columns=["texto_busqueda"], errors="ignore")

    if modo == "General":
        with st.expander("Ver tabla completa de alertas", expanded=False):
            st.dataframe(df_show, width="stretch", hide_index=True)
    else:
        st.dataframe(df_show, width="stretch", hide_index=True)