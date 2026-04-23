from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import numpy as np

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


def _fetch_capm(
    ticker: str,
    start: str,
    end: str,
    benchmark_ticker: str,
    base_currency: str,
    mode: str,
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
            mode=mode,
        )
        return payload, None
    except ApiClientError as exc:
        return {}, exc.message
    except Exception as exc:
        return {}, f"Error inesperado consultando CAPM: {exc}"


def _pick_value(payload: dict | None, *keys):
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _coerce_series_frame(payload: dict) -> pd.DataFrame:
    for key in [
        "regression_points",
        "scatter",
        "points",
        "data",
        "returns_data",
        "observations_data",
        "regression_data",
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

            x_col = pick(
                "benchmark_excess",
                "x",
                "benchmark",
                "benchmark_return",
                "market_excess",
                "market_return",
                "benchmark_excess_return",
            )
            y_col = pick(
                "asset_excess",
                "y",
                "asset",
                "asset_return",
                "asset_excess_return",
                "security_excess",
            )

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
    beta: float | None,
    alpha: float | None,
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
                marker=dict(size=7, opacity=0.72),
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
    return fig

def _format_capm_table(payload: dict) -> pd.DataFrame:
    rows = [
        {"metric": "alpha_diaria", "value": _pick_value(payload, "alpha_daily", "alpha", "alpha_diaria", "alpha_simple")},
        {"metric": "r_squared", "value": _pick_value(payload, "r_squared", "r2", "r2_score")},
        {
            "metric": "expected_return_capm_annual",
            "value": _pick_value(
                payload,
                "expected_return_annual",
                "expected_return_capm_annual",
                "expected_return",
                "capm_expected_return",
            ),
        },
        {"metric": "rf_anual", "value": _pick_value(payload, "risk_free_rate_annual", "rf_annual", "risk_free_rate", "rf_rate_pct")},
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
        return "Cercano al mercado"
    return "Agresivo"


def _beta_interpretation(beta: float | None) -> str:
    if beta is None:
        return "No fue posible estimar beta."
    if beta < 0.8:
        return "Más defensivo que el mercado"
    if beta <= 1.2:
        return "Sensibilidad cercana al benchmark"
    return "Más agresivo que el mercado"


def _alpha_interpretation(alpha: float | None) -> str:
    if alpha is None:
        return "Alpha no disponible"
    if alpha > 0:
        return "Alpha positiva"
    if alpha < 0:
        return "Alpha negativa"
    return "Alpha neutra"


def _r2_interpretation(r2: float | None) -> str:
    if r2 is None:
        return "Ajuste no disponible"
    if r2 < 0.2:
        return "Ajuste bajo"
    if r2 < 0.5:
        return "Ajuste moderado"
    return "Ajuste alto"


def _expected_return_text(v: float | None) -> str:
    if v is None:
        return "N/D"
    try:
        if pd.isna(v):
            return "N/D"
    except Exception:
        pass
    return f"{float(v):.2%}"


def _capm_reading(payload: dict) -> str:
    beta = _pick_value(payload, "beta")
    alpha = _pick_value(payload, "alpha_daily", "alpha", "alpha_diaria", "alpha_simple")
    r2 = _pick_value(payload, "r_squared", "r2", "r2_score")
    exp_ret = _pick_value(payload, "expected_return_annual", "expected_return_capm_annual", "expected_return", "capm_expected_return")
    rf = _pick_value(payload, "risk_free_rate_annual", "rf_annual", "risk_free_rate", "rf_rate_pct")

    beta_text = f"{float(beta):.4f}" if beta is not None else "N/D"
    alpha_text = f"{float(alpha):.6f}" if alpha is not None else "N/D"
    r2_text = f"{float(r2):.4f}" if r2 is not None else "N/D"
    rf_text = f"{float(rf):.2%}" if rf is not None else "N/D"

    return (
        f"La beta de {beta_text} indica un perfil {_beta_interpretation(beta).lower()}, "
        f"el alpha diario estimado es {alpha_text}, y el R² del ajuste es {r2_text}. "
        f"Bajo CAPM, el retorno esperado anual es {_expected_return_text(exp_ret)}, "
        f"frente a una tasa libre de riesgo de {rf_text}."
    )


assets, help_map, load_error = _fetch_assets_and_help()

modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros CAPM",
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
        key="capm_asset_backend",
        help="Selecciona el activo para estimar beta, alpha y retorno esperado bajo CAPM.",
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

    benchmark_ticker = st.text_input(
        "Benchmark",
        value=BENCHMARK_DEFAULT,
        key="capm_benchmark",
        help="Benchmark principal del proyecto: ACWI.",
    )

    base_currency = st.selectbox(
        "Moneda base",
        ["USD", "EUR", "COP"],
        index=0,
        key="capm_base_currency",
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

payload, capm_error = _fetch_capm(
    ticker=ticker,
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
    benchmark_ticker=benchmark_ticker.strip() or BENCHMARK_DEFAULT,
    base_currency=base_currency,
    mode=modo.lower(),
)

header_dashboard(
    "Módulo 4 - CAPM y Beta",
    "Evalúa sensibilidad al mercado, rendimiento esperado y riesgo sistemático del activo",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo muestra qué tan sensible es el activo frente al benchmark y cómo se estima su retorno esperado bajo CAPM."
    )
else:
    nota(
        "En modo estadístico se enfatiza la regresión activo-mercado, la significancia de beta y la lectura técnica de alpha, R² y retorno esperado."
    )

if capm_error:
    st.error(capm_error)
    st.stop()

beta = _pick_value(payload, "beta")
alpha_daily = _pick_value(payload, "alpha_daily", "alpha", "alpha_diaria", "alpha_simple")
r_squared = _pick_value(payload, "r_squared", "r2", "r2_score")
expected_return_annual = _pick_value(
    payload,
    "expected_return_annual",
    "expected_return_capm_annual",
    "expected_return",
    "capm_expected_return",
)
classification = _pick_value(payload, "classification", "clasificacion") or _classify_beta(beta)
points_df = _coerce_series_frame(payload)
table_df = _format_capm_table(payload)

render_meta_row(
    [
        ("Activo", asset_name),
        ("Ticker", ticker),
        ("Benchmark", benchmark_ticker.strip() or BENCHMARK_DEFAULT),
        ("Base", base_currency),
        ("Horizonte", horizonte),
    ]
)

seccion("KPIs CAPM")

c1, c2, c3, c4 = st.columns(4)

with c1:
    tarjeta_kpi(
        "Beta",
        f"{float(beta):.4f}" if beta is not None else "N/D",
        subtexto="Sensibilidad sistemática frente al mercado.",
        help_text=_beta_interpretation(beta),
    )

with c2:
    tarjeta_kpi(
        "Alpha diaria",
        f"{float(alpha_daily):.6f}" if alpha_daily is not None else "N/D",
        subtexto="Exceso de retorno no explicado por la beta.",
        help_text=_alpha_interpretation(alpha_daily),
    )

with c3:
    tarjeta_kpi(
        "R²",
        f"{float(r_squared):.4f}" if r_squared is not None else "N/D",
        subtexto="Capacidad explicativa del ajuste lineal.",
        help_text=_r2_interpretation(r_squared),
    )

with c4:
    tarjeta_kpi(
        "Retorno esperado anual",
        _expected_return_text(expected_return_annual),
        subtexto="Retorno teórico compatible con el riesgo sistemático.",
        help_text="Estimación anual bajo CAPM.",
    )

plot_card_footer(_capm_reading(payload))

# ---- SECCION CLASIFICACION DEL ACTIVO (con tabla integrada) ----
seccion("Clasificación del activo")

render_info_card(
    "Clasificación obtenida",
    f"La clasificación obtenida es: {classification}. Esta etiqueta resume si el activo se comporta de forma más agresiva, defensiva o cercana al mercado.",
)

st.markdown("<div style='height:0.35rem;'></div>", unsafe_allow_html=True)
st.dataframe(table_df, use_container_width=True, hide_index=True)
# ---- FIN SECCION CLASIFICACION ----

seccion("Regresión CAPM")

plot_card_header(
    "Relación activo-mercado",
    "Visualiza la nube de puntos entre el exceso de retorno del benchmark y el exceso del activo.",
    modo=modo,
    caption="Usa los filtros para limpiar la lectura o enfatizar la recta de regresión.",
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
    beta=beta,
    alpha=alpha_daily,
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
    with st.expander("Ver payload CAPM recibido", expanded=False):
        st.json(payload)
else:
    plot_card_footer(
        "La nube de puntos muestra cómo se relacionan los excesos de retorno del activo y del benchmark. La pendiente de la recta resume la beta, mientras que la dispersión alrededor refleja riesgo idiosincrático."
    )