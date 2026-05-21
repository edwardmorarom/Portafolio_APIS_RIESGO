from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_ui import header_dashboard, nota, plot_card_footer, plot_card_header, seccion, tarjeta_kpi
from ui.page_setup import setup_dashboard_page
from ui.plot_style import style_plotly_figure
from ui.portfolio_state import render_portfolio_scope_note


def _format_pct(value: float | None) -> str:
    if value is None:
        return "N/D"
    try:
        return f"{float(value):.2%}"
    except Exception:
        return "N/D"


def _format_num(value: float | None) -> str:
    if value is None:
        return "N/D"
    try:
        return f"{float(value):,.4f}"
    except Exception:
        return "N/D"


def _predict(client, payload: dict) -> dict:
    return client.predict_ml_return(payload)


modo, filtros_panel = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo TomÃ¡s",
    filtros_label="ParÃ¡metros de Machine Learning",
    filtros_expanded=True,
    page_title="Machine Learning",
    page_icon="ðŸ¤–",
)

client = get_api_client()

with filtros_panel:
    render_portfolio_scope_note()
    c1, c2 = st.columns(2)
    with c1:
        volatility = st.number_input("Volatilidad anualizada", min_value=0.0001, max_value=2.0, value=0.22, step=0.01, format="%.4f")
        sharpe_ratio = st.number_input("Sharpe ratio", min_value=-5.0, max_value=10.0, value=1.15, step=0.05, format="%.4f")
        var_95 = st.number_input("VaR 95%", min_value=-1.0, max_value=0.0, value=-0.08, step=0.01, format="%.4f")
    with c2:
        beta = st.number_input("Beta", min_value=-2.0, max_value=5.0, value=1.10, step=0.05, format="%.4f")
        market_return = st.number_input("Retorno esperado del mercado", min_value=-1.0, max_value=1.0, value=0.12, step=0.01, format="%.4f")
        run_prediction = st.button("Ejecutar predicciÃ³n", type="primary", use_container_width=True)

payload = {
    "volatility": float(volatility),
    "sharpe_ratio": float(sharpe_ratio),
    "var_95": float(var_95),
    "beta": float(beta),
    "market_return": float(market_return),
}

header_dashboard(
    "Machine Learning financiero",
    "Criterio 11: pipeline ML, Singleton y endpoint /predict para retorno esperado.",
    modo=modo,
)

render_info_card(
    "QuÃ© predice el modelo",
    (
        "El modelo estima retorno esperado del portafolio a partir de variables financieras derivadas: "
        "volatilidad, Sharpe, VaR 95%, beta y retorno esperado de mercado. Es apoyo predictivo, no prueba causal."
    ),
)

tab_status, tab_prediction, tab_sensitivity, tab_method = st.tabs(["Estado", "PredicciÃ³n", "Sensibilidad", "MetodologÃ­a"])
status: dict | None = None
prediction: float | None = None
prediction_payload: dict = {}
sensitivity: list[tuple[str, float]] = []

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
            ("-25%", 0.75),
            ("-10%", 0.90),
            ("Base", 1.00),
            ("+10%", 1.10),
            ("+25%", 1.25),
        ]
        for label, multiplier in scenarios:
            scenario_payload = dict(payload)
            scenario_payload["volatility"] = max(0.0001, float(payload["volatility"]) * multiplier)
            sensitivity.append((label, float(_predict(client, scenario_payload)["predicted_return"])))
    except ApiClientError as exc:
        st.error(f"Error al consumir el backend ML: {exc.message}")
    except Exception as exc:
        st.error(f"Error inesperado en la predicciÃ³n ML: {exc}")
else:
    nota("Ajusta las variables de riesgo y ejecuta la predicciÃ³n para consultar el modelo backend.")

with tab_status:
    seccion("Estado del modelo")

    if status:
        c1, c2, c3 = st.columns(3)
        with c1:
            tarjeta_kpi("Modelo", "Cargado" if status.get("model_loaded") else "No cargado", subtexto="joblib")
        with c2:
            tarjeta_kpi("VersiÃ³n", str(status.get("model_version", "N/D")), subtexto="ML")
        with c3:
            tarjeta_kpi("TamaÃ±o", f"{status.get('model_size_bytes', 0):,} bytes", subtexto="Archivo persistido")

        render_meta_row(
            {
                "Ruta": status.get("model_path", "N/D"),
                "Modelo": status.get("model_type", "N/D"),
                "Target": status.get("target", "N/D"),
                "Singleton": "SÃ­" if status.get("singleton") else "N/D",
            }
        )
        features = status.get("features", [])
        if features:
            st.dataframe(
                [
                    {
                        "Feature": item,
                        "Uso financiero": {
                            "volatility": "Riesgo total anualizado",
                            "sharpe_ratio": "RelaciÃ³n retorno-riesgo",
                            "var_95": "PÃ©rdida extrema al 95%",
                            "beta": "Sensibilidad al mercado",
                            "market_return": "Escenario de mercado esperado",
                        }.get(item, "Variable financiera"),
                    }
                    for item in features
                ],
                use_container_width=True,
                hide_index=True,
            )
    else:
        render_info_card("Estado no disponible", "No fue posible consultar el endpoint /ml/status.")

with tab_prediction:
    seccion("Resultado predictivo")

    if prediction is not None:
        c1, c2, c3 = st.columns(3)
        with c1:
            tarjeta_kpi("Retorno predicho", _format_pct(prediction), subtexto="Salida del modelo")
        with c2:
            tarjeta_kpi("Volatilidad", _format_pct(volatility), subtexto="Input")
        with c3:
            tarjeta_kpi("VaR 95%", _format_pct(var_95), subtexto="Input")

        render_meta_row(
            {
                "Sharpe": _format_num(sharpe_ratio),
                "Beta": _format_num(beta),
                "Mercado": _format_pct(market_return),
            }
        )

        if prediction > 0.10:
            interpretation = "El modelo estima un retorno favorable frente al nivel de riesgo ingresado."
        elif prediction > 0:
            interpretation = "El modelo estima un retorno positivo, aunque moderado."
        else:
            interpretation = "El modelo estima un retorno bajo o negativo; conviene revisar exposiciÃ³n al riesgo."

        nota(prediction_payload.get("interpretation") or interpretation)
    else:
        render_info_card("PredicciÃ³n pendiente", "Ejecuta el modelo para obtener retorno esperado.")

with tab_sensitivity:
    seccion("Sensibilidad por volatilidad")

    if sensitivity:
        labels = [item[0] for item in sensitivity]
        values = [item[1] for item in sensitivity]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=labels,
                y=values,
                text=[_format_pct(value) for value in values],
                textposition="auto",
                name="Retorno predicho",
            )
        )

        plot_card_header(
            "Escenarios de volatilidad",
            "Muestra cÃ³mo responde el retorno predicho al cambiar la volatilidad base.",
            modo=modo,
        )
        st.plotly_chart(
            style_plotly_figure(
                fig,
                modo=modo,
                title="Sensibilidad del retorno predicho",
                xaxis_title="Escenario",
                yaxis_title="Retorno predicho",
                show_xgrid=False,
            ),
            use_container_width=True,
        )
        plot_card_footer("Esta lectura ayuda a evaluar si la predicciÃ³n depende demasiado del supuesto de volatilidad.")
    else:
        render_info_card("Sensibilidad pendiente", "Ejecuta la predicciÃ³n para construir escenarios.")

with tab_method:
    seccion("Sustento metodológico")
    render_info_card(
        "Justificación del modelo",
        (
            "El modelo de machine learning se usa como complemento predictivo, no como prueba causal. "
            "Se eligió una regresión lineal porque permite explicar el efecto marginal de variables de riesgo "
            "y sirve como línea base transparente para sustentación académica."
        ),
    )
    st.dataframe(
        [
            {"Elemento": "Variable objetivo", "Detalle": "Retorno esperado del portafolio"},
            {"Elemento": "Entrenamiento", "Detalle": "Pipeline reproducible en backend/app/ml/train.py"},
            {"Elemento": "Persistencia", "Detalle": "Modelo guardado en joblib y cargado desde MLPredictor"},
            {"Elemento": "Servicio", "Detalle": "Endpoint /api/v1/ml/predict"},
            {"Elemento": "Singleton", "Detalle": "MLPredictor carga el modelo una sola vez y reutiliza la instancia"},
        ],
        use_container_width=True,
        hide_index=True,
    )
    render_info_card(
        "Supuestos del modelo lineal",
        (
            "La lectura supone relación aproximadamente lineal entre features y retorno, control de multicolinealidad, "
            "errores razonablemente estables y validación fuera de muestra. Si esas condiciones se debilitan, la predicción "
            "debe tratarse solo como apoyo para contrastar riesgo, no como decisión final."
        ),
    )
    render_info_card(
        "Limitaciones",
        (
            "El modelo resume patrones de variables derivadas y no incorpora noticias, liquidez intradía ni cambios estructurales. "
            "Debe compararse con VaR, CAPM, benchmark y stress testing antes de concluir si el portafolio es favorable."
        ),
    )
