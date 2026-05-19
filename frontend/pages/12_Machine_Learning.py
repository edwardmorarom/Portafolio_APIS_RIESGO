from __future__ import annotations

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


def _format_pct(value: float | None) -> str:
    if value is None:
        return "N/D"
    try:
        return f"{float(value):.2%}"
    except Exception:
        return "N/D"


def _build_sensitivity_chart(
    base_payload: dict,
    base_prediction: float,
) -> go.Figure:
    multipliers = [0.75, 0.90, 1.00, 1.10, 1.25]
    labels = ["-25%", "-10%", "Base", "+10%", "+25%"]
    predictions = []

    client = get_api_client()

    for multiplier in multipliers:
        payload = dict(base_payload)
        payload["volatility"] = max(0.0001, float(base_payload["volatility"]) * multiplier)

        try:
            result = client.predict_ml_return(payload)
            predictions.append(float(result["predicted_return"]))
        except Exception:
            predictions.append(base_prediction)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=predictions,
            name="Retorno predicho",
            text=[_format_pct(x) for x in predictions],
            textposition="auto",
        )
    )

    fig.update_layout(
        title="Sensibilidad del retorno predicho ante cambios de volatilidad",
        xaxis_title="Escenario de volatilidad",
        yaxis_title="Retorno predicho",
        showlegend=False,
    )

    return style_plotly_figure(fig)


setup_dashboard_page(
    page_title="Machine Learning",
    page_icon="🤖",
)

header_dashboard(
    title="Machine Learning financiero",
    subtitle="Predicción de retorno esperado usando variables de riesgo, mercado y portafolio.",
)

client = get_api_client()

seccion("Entrada del modelo")

with st.sidebar:
    st.markdown("### Parámetros financieros")

    volatility = st.number_input(
        "Volatilidad anualizada",
        min_value=0.0001,
        max_value=2.0,
        value=0.22,
        step=0.01,
        format="%.4f",
    )

    sharpe_ratio = st.number_input(
        "Sharpe ratio",
        min_value=-5.0,
        max_value=10.0,
        value=1.15,
        step=0.05,
        format="%.4f",
    )

    var_95 = st.number_input(
        "VaR 95%",
        min_value=-1.0,
        max_value=0.0,
        value=-0.08,
        step=0.01,
        format="%.4f",
    )

    beta = st.number_input(
        "Beta",
        min_value=-2.0,
        max_value=5.0,
        value=1.10,
        step=0.05,
        format="%.4f",
    )

    market_return = st.number_input(
        "Retorno esperado del mercado",
        min_value=-1.0,
        max_value=1.0,
        value=0.12,
        step=0.01,
        format="%.4f",
    )

payload = {
    "volatility": float(volatility),
    "sharpe_ratio": float(sharpe_ratio),
    "var_95": float(var_95),
    "beta": float(beta),
    "market_return": float(market_return),
}

render_info_card(
    "Modelo ML integrado",
    "El modelo usa un pipeline entrenado en backend, persistido con joblib y expuesto mediante FastAPI.",
)

try:
    status = client.get("/ml/status")
    render_meta_row(
        {
            "Modelo cargado": "Sí" if status.get("model_loaded") else "No",
            "Versión": status.get("model_version", "N/D"),
            "Tamaño": f"{status.get('model_size_bytes', 0)} bytes",
        }
    )
except ApiClientError as exc:
    st.warning(f"No fue posible consultar el estado del modelo ML: {exc.message}")

if st.button("Ejecutar predicción ML", type="primary"):
    try:
        result = client.predict_ml_return(payload)
        predicted_return = float(result["predicted_return"])

        seccion("Resultado de predicción")

        col1, col2, col3 = st.columns(3)
        with col1:
            tarjeta_kpi("Retorno predicho", _format_pct(predicted_return))
        with col2:
            tarjeta_kpi("Volatilidad", _format_pct(volatility))
        with col3:
            tarjeta_kpi("VaR 95%", _format_pct(var_95))

        if predicted_return > 0.10:
            interpretation = "El modelo estima un retorno favorable frente al nivel de riesgo ingresado."
        elif predicted_return > 0:
            interpretation = "El modelo estima un retorno positivo, aunque moderado."
        else:
            interpretation = "El modelo estima un retorno bajo o negativo; se recomienda revisar exposición al riesgo."

        nota(interpretation)

        seccion("Sensibilidad")

        plot_card_header("Escenarios de volatilidad")
        fig = _build_sensitivity_chart(payload, predicted_return)
        st.plotly_chart(fig, use_container_width=True)
        plot_card_footer("La gráfica muestra cómo cambia la predicción al modificar la volatilidad base.")

    except ApiClientError as exc:
        st.error(f"Error al consumir el backend ML: {exc.message}")
    except Exception as exc:
        st.error(f"Error inesperado en la predicción ML: {exc}")
else:
    nota("Ajusta los parámetros en la barra lateral y ejecuta la predicción para consultar el modelo backend.")
