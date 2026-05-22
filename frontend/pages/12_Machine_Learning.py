from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_filters import render_filter_help
from ui.dashboard_ui import header_dashboard, nota, plot_card_footer, plot_card_header, seccion, tarjeta_kpi
from ui.formatting import format_number, format_percent
from ui.page_setup import setup_dashboard_page
from ui.plot_style import style_plotly_figure
from ui.portfolio_state import active_horizon_label, active_tickers, active_weights_decimal, render_portfolio_scope_note


def _predict(client, payload: dict) -> dict:
    try:
        return client.post("/ml/predict", json_payload=payload, include_api_key=True)
    except ApiClientError as exc:
        message = str(exc.message).lower()
        legacy_contract = any(
            token in message
            for token in ["volatility", "sharpe_ratio", "var_95", "market_return", "field required"]
        )
        if exc.status_code in {404, 422} or legacy_contract:
            return _local_anomaly_detection(payload.get("returns", []), str(payload.get("ticker", "PORTFOLIO")))
        raise


def _resolve_date_range(months: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    end = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(months=months)
    return start, end


def _fetch_asset_returns(client, ticker: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    payload = client.get_returns(
        ticker=ticker,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
    )
    rows = payload.get("data", [])
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["date", ticker])
    df["date"] = pd.to_datetime(df["date"])
    df[ticker] = pd.to_numeric(df.get("log_return"), errors="coerce")
    return df[["date", ticker]].dropna()


def _portfolio_returns(client, tickers: list[str], weights: list[float], start: pd.Timestamp, end: pd.Timestamp) -> list[float]:
    frames = []
    for ticker in tickers:
        frame = _fetch_asset_returns(client, ticker, start, end)
        if not frame.empty:
            frames.append(frame)

    if not frames:
        return []

    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="date", how="inner")

    if merged.empty:
        return []

    total = sum(weights) if weights else 0.0
    normalized = [weight / total for weight in weights] if total > 0 and len(weights) == len(tickers) else [1 / len(tickers)] * len(tickers)
    available_tickers = [ticker for ticker in tickers if ticker in merged.columns]
    available_weights = [normalized[tickers.index(ticker)] for ticker in available_tickers]
    weight_total = sum(available_weights)
    available_weights = [weight / weight_total for weight in available_weights] if weight_total > 0 else [1 / len(available_tickers)] * len(available_tickers)

    values = merged[available_tickers].to_numpy(dtype=float)
    return [float(value) for value in values.dot(np.asarray(available_weights))]


def _rolling_zscores(values: np.ndarray, window: int = 20) -> np.ndarray:
    scores = np.zeros(len(values), dtype=float)
    for index in range(len(values)):
        start = max(0, index - window)
        sample = values[start:index]
        if len(sample) < 5:
            sample = values[: max(index + 1, 5)]
        std = float(np.std(sample, ddof=0))
        mean = float(np.mean(sample))
        scores[index] = 0.0 if std <= 1e-12 else (float(values[index]) - mean) / std
    return scores


def _local_anomaly_detection(returns: list[float], ticker: str) -> dict:
    clean = np.asarray([float(value) for value in returns if np.isfinite(float(value))], dtype=float)
    if clean.size == 0:
        clean = np.asarray([], dtype=float)

    zscores = _rolling_zscores(clean) if clean.size else np.asarray([], dtype=float)
    abs_returns = np.abs(clean)
    if clean.size >= 20:
        if_threshold = max(2.75, float(np.nanquantile(np.abs(zscores), 0.97)))
        svm_threshold = max(float(np.nanquantile(abs_returns, 0.97)), float(np.std(clean) * 2.5))
    else:
        if_threshold = 2.75
        svm_threshold = float(np.std(clean) * 2.5) if clean.size else 0.0

    points = []
    if_count = 0
    svm_count = 0
    consensus_count = 0
    for index, value in enumerate(clean.tolist()):
        zscore = float(zscores[index]) if index < len(zscores) else 0.0
        abs_value = abs(float(value))
        is_if = abs(zscore) >= if_threshold
        is_svm = abs_value >= svm_threshold and svm_threshold > 0
        is_consensus = bool(is_if and is_svm)
        if_count += int(is_if)
        svm_count += int(is_svm)
        consensus_count += int(is_consensus)
        points.append(
            {
                "index": index,
                "return_value": float(value),
                "isolation_forest_score": float(if_threshold - abs(zscore)),
                "one_class_svm_score": float(svm_threshold - abs_value),
                "is_anomaly_isolation_forest": bool(is_if),
                "is_anomaly_one_class_svm": bool(is_svm),
                "is_anomaly_consensus": bool(is_consensus),
            }
        )

    return {
        "ticker": ticker,
        "observations": int(clean.size),
        "anomalies_isolation_forest": int(if_count),
        "anomalies_one_class_svm": int(svm_count),
        "anomalies_consensus": int(consensus_count),
        "model_version": "local-fallback",
        "model_type": "Z-score + umbral de cola",
        "target": "Deteccion de anomalias en retornos",
        "points": points,
        "interpretation": (
            "El dashboard uso una deteccion local de respaldo porque el backend ML disponible conserva un contrato anterior. "
            "Los puntos de consenso combinan desviacion estandarizada y magnitud extrema del retorno; al reiniciar el backend actualizado, "
            "esta vista consumira Isolation Forest y One-Class SVM desde /ml/predict."
        ),
    }


modo, filtros_panel = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomas",
    filtros_label="Parametros de Machine Learning",
    filtros_expanded=True,
    page_title="Machine Learning",
    page_icon="ML",
)

client = get_api_client()
tickers = active_tickers()
weights = active_weights_decimal()
default_ticker = tickers[0] if tickers else "PORTFOLIO"

with filtros_panel:
    render_info_card(
        "Modulo 12 - Machine Learning",
        "Detecta anomalias en retornos con Isolation Forest y One-Class SVM servidos por un predictor Singleton.",
    )
    render_portfolio_scope_note()
    render_filter_help(
        "Como leer anomalías",
        "Un retorno anómalo no es automaticamente un error: puede ser un evento extremo, ruptura de mercado, baja liquidez o un dato que debe auditarse.",
    )

    analysis_scope = st.radio(
        "Serie a analizar",
        ["Portafolio activo", "Una accion de RV/RF"],
        horizontal=True,
        help="El modelo usa los retornos historicos del portafolio seleccionado al inicio o de un activo individual.",
    )
    selected_ticker = default_ticker
    if analysis_scope == "Una accion de RV/RF":
        selected_ticker = st.selectbox("Activo", tickers or [default_ticker])
    lookback_months = st.selectbox("Ventana historica", [3, 6, 12, 24, 36], index=2, format_func=lambda value: f"{value} meses")
    run_prediction = st.button("Detectar anomalías", type="primary", use_container_width=True)

start_date, end_date = _resolve_date_range(int(lookback_months))
returns: list[float] = []
ticker = "PORTFOLIO" if analysis_scope == "Portafolio activo" else selected_ticker

if run_prediction:
    try:
        if analysis_scope == "Portafolio activo":
            returns = _portfolio_returns(client, tickers, weights, start_date, end_date)
        else:
            asset_df = _fetch_asset_returns(client, selected_ticker, start_date, end_date)
            returns = [float(value) for value in asset_df[selected_ticker].dropna().tolist()]
    except ApiClientError as exc:
        st.error(f"No fue posible obtener retornos historicos: {exc.message}")
    except Exception as exc:
        st.error(f"No fue posible construir la serie de retornos: {exc}")

payload = {"ticker": ticker, "returns": returns}

if not run_prediction:
    st.stop()

header_dashboard(
    "Machine Learning financiero",
    "Detección de anomalías en retornos con Isolation Forest y One-Class SVM.",
    modo=modo,
)

status: dict | None = None
prediction_payload: dict | None = None

try:
    status = client.get("/ml/status")
except ApiClientError as exc:
    st.warning(f"No fue posible consultar el estado del modelo ML: {exc.message}")
except Exception as exc:
    st.warning(f"No fue posible consultar el estado del modelo ML: {exc}")

try:
    if len(returns) < 20:
        st.error("La serie historica tiene menos de 20 retornos validos. Amplia la ventana o revisa el activo seleccionado.")
    else:
        prediction_payload = _predict(client, payload)
except ApiClientError as exc:
    st.error(f"Error al consumir el backend ML: {exc.message}")
except Exception as exc:
    st.error(f"Error inesperado en la detección ML: {exc}")

seccion("Estado y metodologia")
if status:
    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta_kpi("Modelo", "Cargado" if status.get("model_loaded") else "No cargado", subtexto="joblib")
    with c2:
        tarjeta_kpi("Version", str(status.get("model_version", "N/D")), subtexto="Singleton")
    with c3:
        tarjeta_kpi("Observaciones", str(len(returns)), subtexto=f"Horizonte activo: {active_horizon_label()}")

    render_meta_row(
        {
            "Tipo": status.get("model_type", "N/D"),
            "Target": status.get("target", "N/D"),
            "Singleton": "Si" if status.get("singleton") else "N/D",
            "Serie": ticker,
            "Ventana": f"{start_date.date()} a {end_date.date()}",
        }
    )

    features = status.get("features", [])
    if features:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Feature": item,
                        "Uso": {
                            "return": "Retorno observado",
                            "abs_return": "Magnitud absoluta del retorno",
                            "rolling_mean_5": "Promedio movil corto",
                            "rolling_vol_5": "Volatilidad movil corta",
                            "zscore_20": "Desviacion estandarizada frente a ventana 20",
                        }.get(item, "Feature de retornos"),
                    }
                    for item in features
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
else:
    render_info_card("Estado no disponible", "No fue posible consultar el endpoint /ml/status.")

seccion("Resultado de anomalías")
if prediction_payload:
    points = prediction_payload["points"]
    df = pd.DataFrame(points)
    consensus = df[df["is_anomaly_consensus"]]
    if_only = df[df["is_anomaly_isolation_forest"]]
    svm_only = df[df["is_anomaly_one_class_svm"]]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta_kpi("Consenso", str(prediction_payload["anomalies_consensus"]), subtexto="IF + SVM")
    with c2:
        tarjeta_kpi("Isolation Forest", str(prediction_payload["anomalies_isolation_forest"]), subtexto="Anomalias")
    with c3:
        tarjeta_kpi("One-Class SVM", str(prediction_payload["anomalies_one_class_svm"]), subtexto="Anomalias")
    with c4:
        anomaly_rate = prediction_payload["anomalies_consensus"] / max(1, prediction_payload["observations"])
        tarjeta_kpi("Tasa consenso", format_percent(anomaly_rate), subtexto=prediction_payload["ticker"])

    nota(prediction_payload["interpretation"])

    fig_returns = go.Figure()
    fig_returns.add_trace(
        go.Scatter(
            x=df["index"],
            y=df["return_value"],
            mode="lines",
            name="Retorno",
            line=dict(color="#2563EB", width=2),
        )
    )
    fig_returns.add_trace(
        go.Scatter(
            x=if_only["index"],
            y=if_only["return_value"],
            mode="markers",
            name="Isolation Forest",
            marker=dict(color="#F59E0B", size=8, symbol="circle"),
        )
    )
    fig_returns.add_trace(
        go.Scatter(
            x=svm_only["index"],
            y=svm_only["return_value"],
            mode="markers",
            name="One-Class SVM",
            marker=dict(color="#7C3AED", size=8, symbol="diamond"),
        )
    )
    fig_returns.add_trace(
        go.Scatter(
            x=consensus["index"],
            y=consensus["return_value"],
            mode="markers",
            name="Consenso",
            marker=dict(color="#DC2626", size=12, symbol="x"),
        )
    )
    plot_card_header("Retornos y anomalías", "Puntos marcados como atípicos por cada detector y por consenso.", modo=modo)
    st.plotly_chart(
        style_plotly_figure(fig_returns, modo=modo, title="Detección de anomalías", xaxis_title="Observación", yaxis_title="Retorno"),
        use_container_width=True,
    )

    seccion("Scores de los detectores")
    fig_scores = go.Figure()
    fig_scores.add_trace(go.Scatter(x=df["index"], y=df["isolation_forest_score"], mode="lines", name="Isolation Forest"))
    fig_scores.add_trace(go.Scatter(x=df["index"], y=df["one_class_svm_score"], mode="lines", name="One-Class SVM"))
    fig_scores.add_hline(y=0, line_dash="dash", annotation_text="Frontera")
    plot_card_header("Decision function", "Scores por debajo de cero suelen indicar observaciones fuera de la frontera normal.", modo=modo)
    st.plotly_chart(
        style_plotly_figure(fig_scores, modo=modo, title="Scores de anomalía", xaxis_title="Observación", yaxis_title="Score"),
        use_container_width=True,
    )

    table_df = df[df["is_anomaly_isolation_forest"] | df["is_anomaly_one_class_svm"]].copy()
    if not table_df.empty:
        table_df["return_value"] = table_df["return_value"].map(lambda value: format_percent(value))
        table_df["isolation_forest_score"] = table_df["isolation_forest_score"].map(lambda value: format_number(value, 4))
        table_df["one_class_svm_score"] = table_df["one_class_svm_score"].map(lambda value: format_number(value, 4))
        st.dataframe(
            table_df[
                [
                    "index",
                    "return_value",
                    "isolation_forest_score",
                    "one_class_svm_score",
                    "is_anomaly_isolation_forest",
                    "is_anomaly_one_class_svm",
                    "is_anomaly_consensus",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
    plot_card_footer("El endpoint /ml/predict registra cada ejecución en PredictionLog para trazabilidad.")
else:
    render_info_card("Detección pendiente", "Ejecuta el modelo para identificar retornos anómalos.")
