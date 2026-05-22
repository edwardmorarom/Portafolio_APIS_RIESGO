from __future__ import annotations

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
from ui.portfolio_state import active_horizon_label, render_portfolio_scope_note


MODEL_LABELS = {
    "ridge": "Ridge",
    "lasso": "Lasso",
    "gradient_boosting": "Gradient Boosting",
}


def _predict(client, payload: dict) -> dict:
    return client.predict_ml_return(payload)


modo, filtros_panel = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomas",
    filtros_label="Parametros de Machine Learning",
    filtros_expanded=True,
    page_title="Machine Learning",
    page_icon="ML",
)

client = get_api_client()

with filtros_panel:
    render_info_card(
        "Modulo 12 - Machine Learning",
        "Predice retorno acumulado a horizonte fijo con Ridge, Lasso y Gradient Boosting como apoyo al analisis de riesgo.",
    )
    render_portfolio_scope_note()
    render_filter_help(
        "Como llenar Machine Learning",
        "El modelo predice retorno acumulado para un horizonte fijo. Volatilidad, Sharpe, VaR, beta y retorno de mercado son inputs financieros; el horizonte define cuantos meses acumula la prediccion.",
    )
    c1, c2 = st.columns(2)
    with c1:
        horizon_months = st.selectbox("Horizonte fijo de prediccion", [1, 3, 6, 12, 24, 36], index=3, help="Meses sobre los que se acumula el retorno predicho.")
        model_name = st.selectbox("Modelo principal", list(MODEL_LABELS.keys()), index=2, format_func=lambda key: MODEL_LABELS[key], help="Ridge y Lasso son lineales regularizados; Gradient Boosting captura patrones no lineales.")
        volatility = st.number_input("Volatilidad anualizada", min_value=0.0001, max_value=2.0, value=0.22, step=0.01, format="%.4f", help="Riesgo total anualizado usado como feature del modelo.")
        sharpe_ratio = st.number_input("Sharpe ratio", min_value=-5.0, max_value=10.0, value=1.15, step=0.05, format="%.4f", help="Relacion retorno-riesgo esperada del portafolio.")
    with c2:
        var_95 = st.number_input("VaR 95%", min_value=-1.0, max_value=0.0, value=-0.08, step=0.01, format="%.4f", help="Perdida extrema estimada que resume riesgo de cola.")
        beta = st.number_input("Beta", min_value=-2.0, max_value=5.0, value=1.10, step=0.05, format="%.4f", help="Sensibilidad del portafolio frente al benchmark.")
        market_return = st.number_input("Retorno esperado del mercado", min_value=-1.0, max_value=1.0, value=0.12, step=0.01, format="%.4f", help="Escenario de retorno del benchmark o mercado de referencia.")
        run_prediction = st.button("Ejecutar prediccion", type="primary", use_container_width=True)

payload = {
    "volatility": float(volatility),
    "sharpe_ratio": float(sharpe_ratio),
    "var_95": float(var_95),
    "beta": float(beta),
    "market_return": float(market_return),
    "horizon_months": int(horizon_months),
    "model_name": model_name,
}

header_dashboard(
    "Machine Learning financiero",
    "Prediccion de retorno acumulado a horizonte fijo con Ridge, Lasso y Gradient Boosting.",
    modo=modo,
)

render_info_card(
    "Que predice el modelo",
    (
        "El modelo estima el retorno acumulado del portafolio para un horizonte fijo. "
        "Compara Ridge, Lasso y Gradient Boosting usando variables de riesgo y mercado. "
        "La prediccion es apoyo analitico, no recomendacion automatica."
    ),
)

status: dict | None = None
prediction_payload: dict = {}
prediction: float | None = None
sensitivity: list[dict] = []

try:
    status = client.get("/ml/status")
except ApiClientError as exc:
    st.warning(f"No fue posible consultar el estado del modelo ML: {exc.message}")
except Exception as exc:
    st.warning(f"No fue posible consultar el estado del modelo ML: {exc}")

if run_prediction:
    try:
        prediction_payload = _predict(client, payload)
        prediction = float(prediction_payload["predicted_return"])
        scenarios = [
            ("Base", {}),
            ("Mercado -10%", {"market_return": market_return - 0.10}),
            ("Mercado +10%", {"market_return": market_return + 0.10}),
            ("Volatilidad baja", {"volatility": max(0.0001, volatility * 0.70)}),
            ("Volatilidad alta", {"volatility": min(2.0, volatility * 1.35)}),
            ("Beta alta", {"beta": min(5.0, beta + 0.35)}),
        ]
        for label, overrides in scenarios:
            scenario_payload = dict(payload)
            scenario_payload.update({key: float(value) for key, value in overrides.items()})
            response = _predict(client, scenario_payload)
            sensitivity.append({"Escenario": label, "Retorno predicho": float(response["predicted_return"])})
    except ApiClientError as exc:
        st.error(f"Error al consumir el backend ML: {exc.message}")
    except Exception as exc:
        st.error(f"Error inesperado en la prediccion ML: {exc}")
else:
    nota("Ajusta las variables de riesgo y ejecuta la prediccion para consultar el modelo backend.")

seccion("Estado y metodologia")
if status:
    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta_kpi("Modelo", "Cargado" if status.get("model_loaded") else "No cargado", subtexto="joblib", help_text="Indica si el backend cargo el artefacto del modelo desde disco.")
    with c2:
        tarjeta_kpi("Version", str(status.get("model_version", "N/D")), subtexto="ML", help_text="Version del pipeline usada para entrenar y servir la prediccion.")
    with c3:
        tarjeta_kpi("Horizonte", f"{horizon_months} meses", subtexto=f"Inicial: {active_horizon_label()}", help_text="Plazo fijo para acumular el retorno predicho.")

    render_meta_row(
        {
            "Tipo": status.get("model_type", "N/D"),
            "Target": status.get("target", "N/D"),
            "Singleton": "Si" if status.get("singleton") else "N/D",
            "Modelo principal": MODEL_LABELS[model_name],
        }
    )

    features = status.get("features", [])
    if features:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Feature": item,
                        "Uso financiero": {
                            "volatility": "Riesgo total anualizado",
                            "sharpe_ratio": "Relacion retorno-riesgo",
                            "var_95": "Perdida extrema al 95%",
                            "beta": "Sensibilidad al benchmark",
                            "market_return": "Escenario de mercado esperado",
                            "horizon_months": "Plazo fijo de acumulacion",
                        }.get(item, "Variable financiera"),
                    }
                    for item in features
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
else:
    render_info_card("Estado no disponible", "No fue posible consultar el endpoint /ml/status.")

seccion("Prediccion de retorno acumulado")
if prediction is not None:
    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta_kpi("Retorno acumulado", format_percent(prediction), subtexto=MODEL_LABELS[model_name], help_text="Prediccion del retorno total acumulado para el horizonte seleccionado.")
    with c2:
        tarjeta_kpi("Volatilidad", format_percent(volatility), subtexto="Input", help_text="Feature de riesgo total enviada al modelo.")
    with c3:
        tarjeta_kpi("VaR 95%", format_percent(var_95), subtexto="Input", help_text="Feature de perdida extrema enviada al modelo.")

    render_meta_row({"Sharpe": format_number(sharpe_ratio), "Beta": format_number(beta), "Mercado": format_percent(market_return)})
    nota(prediction_payload.get("interpretation", "Prediccion calculada correctamente."))

    model_predictions = prediction_payload.get("model_predictions", {})
    if model_predictions:
        compare_df = pd.DataFrame(
            [{"Modelo": MODEL_LABELS.get(key, key), "Retorno acumulado": value} for key, value in model_predictions.items()]
        )
        fig_models = go.Figure()
        fig_models.add_trace(
            go.Bar(
                x=compare_df["Modelo"],
                y=compare_df["Retorno acumulado"],
                text=[format_percent(value) for value in compare_df["Retorno acumulado"]],
                textposition="auto",
                name="Prediccion",
            )
        )
        plot_card_header("Comparacion de modelos", "Ridge y Lasso aportan linea base regularizada; Gradient Boosting captura relaciones no lineales.", modo=modo)
        st.plotly_chart(
            style_plotly_figure(fig_models, modo=modo, title="Retorno acumulado por modelo", xaxis_title="Modelo", yaxis_title="Retorno acumulado", show_xgrid=False),
            use_container_width=True,
        )
else:
    render_info_card("Prediccion pendiente", "Ejecuta el modelo para obtener retorno acumulado a horizonte fijo.")

seccion("Sensibilidad por escenarios")
if sensitivity:
    sens_df = pd.DataFrame(sensitivity)
    fig_h = go.Figure()
    fig_h.add_trace(
        go.Bar(
            x=sens_df["Escenario"],
            y=sens_df["Retorno predicho"],
            name=MODEL_LABELS[model_name],
            text=[format_percent(value) for value in sens_df["Retorno predicho"]],
            textposition="auto",
        )
    )
    plot_card_header("Escenarios ML", "Muestra como cambia la prediccion cuando se alteran mercado, volatilidad o beta.", modo=modo)
    st.plotly_chart(
        style_plotly_figure(fig_h, modo=modo, title="Sensibilidad del retorno acumulado", xaxis_title="Escenario", yaxis_title="Retorno acumulado", show_xgrid=False),
        use_container_width=True,
    )
    plot_card_footer("La grafica ya no es fija: responde a cambios en las variables financieras enviadas al endpoint /predict.")
else:
    render_info_card("Sensibilidad pendiente", "Ejecuta la prediccion para construir escenarios de mercado y volatilidad.")

seccion("Sustento para exposicion")
render_info_card(
    "Por que estos modelos",
    (
        "Ridge reduce inestabilidad por multicolinealidad, Lasso puede disminuir el peso de variables poco utiles y "
        "Gradient Boosting captura relaciones no lineales entre riesgo, beta, mercado y retorno acumulado."
    ),
)
render_info_card(
    "Supuestos y limites",
    (
        "Ridge/Lasso requieren una relacion aproximadamente estable entre variables y retorno. Gradient Boosting no exige linealidad, "
        "pero requiere controlar sobreajuste y revisar metricas fuera de muestra. Ningun modelo prueba causalidad ni reemplaza VaR, CAPM o stress testing."
    ),
)
