from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_meta_row, render_info_card
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


def _fetch_garch(
    ticker: str,
    start: str,
    end: str,
    return_type: str,
    mode: str,
    forecast_horizon: int,
    distribution: str,
) -> tuple[dict, str | None]:
    client = get_api_client()

    try:
        payload = client.get_garch(
            ticker=ticker,
            start=start,
            end=end,
            return_type=return_type,
            mode=mode,
            forecast_horizon=forecast_horizon,
            distribution=distribution,
        )
        return payload, None
    except ApiClientError as exc:
        return {}, exc.message


def _format_comparison_table(candidate_models: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(candidate_models)
    if df.empty:
        return pd.DataFrame()

    rename_map = {
        "model_name": "Modelo",
        "log_likelihood": "LogLik",
        "aic": "AIC",
        "bic": "BIC",
    }
    df = df.rename(columns=rename_map)

    for col in ["LogLik", "AIC", "BIC"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(4)

    return df.sort_values("AIC").reset_index(drop=True)


def _extract_best_log_likelihood(payload: dict):
    direct_value = (
        payload.get("best_model_log_likelihood")
        or payload.get("best_log_likelihood")
        or payload.get("log_likelihood")
        or payload.get("loglikelihood")
        or payload.get("llf")
    )

    if direct_value is not None:
        return direct_value

    best_model = str(payload.get("best_model", "")).strip().lower()
    candidate_models = payload.get("candidate_models", []) or []

    for model in candidate_models:
        model_name = str(
            model.get("model_name")
            or model.get("name")
            or model.get("model")
            or ""
        ).strip().lower()

        if model_name == best_model:
            return (
                model.get("log_likelihood")
                or model.get("loglikelihood")
                or model.get("log_lik")
                or model.get("llf")
            )

    return None 


def _format_diagnostics_table(payload: dict) -> pd.DataFrame:
    rows = [
        {"Métrica": "Observaciones", "Valor": payload.get("observations")},
        {"Métrica": "Mejor modelo", "Valor": payload.get("best_model")},
        {"Métrica": "Distribución", "Valor": payload.get("distribution_label", "Normal")},
        {"Métrica": "AIC", "Valor": payload.get("best_model_aic")},
        {"Métrica": "BIC", "Valor": payload.get("best_model_bic")},
        {"Métrica": "JB residuos", "Valor": payload.get("residuals_jarque_bera_stat")},
        {"Métrica": "JB p-value residuos", "Valor": payload.get("residuals_jarque_bera_p_value")},
        {"Métrica": "Conclusión normalidad", "Valor": payload.get("residuals_normality_conclusion")},
        {"Métrica": "Horizonte efectivo", "Valor": payload.get("effective_forecast_horizon")},
    ]

    df = pd.DataFrame(rows)

    def _fmt(v):
        if v is None:
            return "N/D"
        try:
            return f"{float(v):.6f}"
        except Exception:
            return str(v)

    df["Valor"] = df["Valor"].apply(_fmt)
    return df


def _extract_best_model_series(payload: dict) -> pd.DataFrame:
    cond_vol = payload.get("conditional_volatility", []) or []
    if not cond_vol:
        return pd.DataFrame(columns=["x", "y", "model"])

    df = pd.DataFrame(
        {
            "x": list(range(1, len(cond_vol) + 1)),
            "y": pd.to_numeric(cond_vol, errors="coerce"),
            "model": str(payload.get("best_model", "Mejor modelo")),
        }
    ).dropna()

    return df


def _extract_multi_model_series(payload: dict) -> pd.DataFrame:
    """
    Intenta encontrar trayectorias por modelo en distintos formatos posibles.
    Si el backend no las devuelve, retorna vacío y el frontend cae al mejor modelo.
    """
    possible_keys = [
        "conditional_volatility_by_model",
        "candidate_model_volatility",
        "model_conditional_volatility",
        "volatility_by_model",
        "series_by_model",
    ]

    for key in possible_keys:
        block = payload.get(key)
        if isinstance(block, dict) and block:
            rows: list[dict] = []
            for model_name, values in block.items():
                if isinstance(values, list) and values:
                    for i, value in enumerate(values, start=1):
                        try:
                            y = float(value)
                        except Exception:
                            continue
                        rows.append({"x": i, "y": y, "model": str(model_name)})
            df = pd.DataFrame(rows)
            if not df.empty:
                return df

    return pd.DataFrame(columns=["x", "y", "model"])


def _build_conditional_volatility_figure(payload: dict, modo: str) -> tuple[go.Figure, bool]:
    series_df = _extract_multi_model_series(payload)
    has_multiple_models = not series_df.empty and series_df["model"].nunique() > 1

    if series_df.empty:
        series_df = _extract_best_model_series(payload)

    fig = go.Figure()

    if not series_df.empty:
        for model_name in series_df["model"].dropna().unique():
            part = series_df[series_df["model"] == model_name]
            fig.add_trace(
                go.Scatter(
                    x=part["x"],
                    y=part["y"],
                    mode="lines",
                    name=str(model_name),
                    line=dict(width=2.4),
                )
            )

    fig = style_plotly_figure(
        fig,
        modo=modo,
        title="Volatilidad condicional estimada",
        xaxis_title="Observación",
        yaxis_title="Volatilidad",
        show_xgrid=True,
        show_ygrid=True,
    )

    return fig, has_multiple_models

def compact_help_card(title: str, help_text: str, caption: str = ""):
    caption_html = (
        f'<div style="font-size:0.92rem;color:var(--text-soft);font-weight:600;line-height:1.45;margin-top:0.35rem;">{caption}</div>'
        if caption
        else ""
    )

    st.markdown(
        f"""
        <div class="ui-plot-head">
            <div class="ui-plot-head-top">
                <div style="display:flex;align-items:center;gap:0.35rem;margin:0;">
                    <div class="ui-plot-title">{title}</div>
                    <span class="ui-help" title="{help_text}">?</span>
                </div>
            </div>
            {caption_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

def _extract_forecast_df(payload: dict) -> pd.DataFrame:
    forecast = payload.get("forecast", []) or []
    if not forecast:
        return pd.DataFrame(columns=["step", "volatility"])

    df = pd.DataFrame(forecast)

    if "step" not in df.columns:
        df["step"] = range(1, len(df) + 1)

    if "volatility" not in df.columns:
        return pd.DataFrame(columns=["step", "volatility"])

    df["step"] = pd.to_numeric(df["step"], errors="coerce")
    df["volatility"] = pd.to_numeric(df["volatility"], errors="coerce")
    df = df.dropna(subset=["step", "volatility"]).reset_index(drop=True)
    return df


def _build_forecast_figure(
    forecast_df: pd.DataFrame,
    modo: str,
    clean_view: bool,
) -> go.Figure:
    fig = go.Figure()

    if not forecast_df.empty:
        x_vals = forecast_df["step"]
        y_vals = forecast_df["volatility"]

        # Punto principal
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="markers",
                name="Volatilidad esperada",
                marker=dict(
                    size=12 if len(forecast_df) == 1 else 9,
                    color="#1D4ED8",
                ),
            )
        )

        # Línea de referencia / trayectoria
        if len(forecast_df) == 1:
            fig.add_trace(
                go.Scatter(
                    x=[float(x_vals.iloc[0]) - 0.45, float(x_vals.iloc[0]) + 0.45],
                    y=[float(y_vals.iloc[0]), float(y_vals.iloc[0])],
                    mode="lines",
                    name="Referencia 1 paso",
                    line=dict(
                        width=2.2,
                        dash="dot",
                        color="#8A1538",
                    ),
                )
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines",
                    name="Trayectoria forecast",
                    line=dict(
                        width=2.4,
                        dash="dot",
                        color="#8A1538",
                    ),
                )
            )

    fig = style_plotly_figure(
        fig,
        modo=modo,
        title="Pronóstico de volatilidad",
        xaxis_title="Horizonte",
        yaxis_title="Volatilidad",
        show_xgrid=not clean_view,
        show_ygrid=not clean_view,
    )

    return fig


def _forecast_message(payload: dict) -> str:
    forecast_df = _extract_forecast_df(payload)
    eff_h = payload.get("effective_forecast_horizon")

    if forecast_df.empty:
        return "El backend no devolvió una trayectoria de forecast utilizable."

    if len(forecast_df) == 1 or eff_h == 1:
        point = float(forecast_df.iloc[0]["volatility"])
        return (
            f"El backend entregó un forecast efectivo de un solo paso. "
            f"Por eso el gráfico muestra un nivel puntual y no una trayectoria completa. "
            f"La volatilidad esperada inmediata es {point:.4f}."
        )

    first_v = float(forecast_df.iloc[0]["volatility"])
    last_v = float(forecast_df.iloc[-1]["volatility"])

    return (
        f"El pronóstico cubre {len(forecast_df)} pasos. "
        f"Parte desde {first_v:.4f} y termina en {last_v:.4f}. "
        f"Úsalo para evaluar si la volatilidad tendería a subir, bajar o estabilizarse."
    )


def _diagnostic_guide(payload: dict) -> str:
    model = str(payload.get("best_model", "N/D"))
    dist_label = str(payload.get("distribution_label", "Normal"))
    aic = payload.get("best_model_aic")
    bic = payload.get("best_model_bic")
    jb_p = payload.get("residuals_jarque_bera_p_value")
    normality = str(payload.get("residuals_normality_conclusion", ""))
    obs = payload.get("observations")

    aic_text = f"{float(aic):.4f}" if aic is not None else "N/D"
    bic_text = f"{float(bic):.4f}" if bic is not None else "N/D"
    jb_text = f"{float(jb_p):.6f}" if jb_p is not None else "N/D"

    normality_read = (
        "Los residuos aún parecen alejarse de normalidad."
        if "rechaza" in normality.lower()
        else "No hay evidencia fuerte contra la normalidad de residuos."
    )

    return (
        f"Para diagnosticar el ajuste, primero identifica el modelo ganador: {model} con errores {dist_label}. "
        f"Luego revisa AIC={aic_text} y BIC={bic_text}; valores más bajos favorecen ese ajuste frente a los demás. "
        f"Después observa el test de Jarque-Bera sobre residuos estandarizados: p-value={jb_text}. "
        f"{normality_read} Finalmente, valida que el número de observaciones ({obs}) sea razonable para sustentar el ajuste."
    )


assets, help_map, load_error = _fetch_assets_and_help()

modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros GARCH",
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
        "Activo representativo",
        options=asset_labels,
        key="garch_asset_backend",
        help="Selecciona el activo para ajustar y comparar modelos ARCH/GARCH/EGARCH.",
    )

    horizonte = st.selectbox(
        "Horizonte de análisis",
        ["1 mes", "Trimestre", "Semestre", "1 año", "3 años", "5 años", "Personalizado"],
        index=3,
        key="garch_horizonte_backend",
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
                key="garch_custom_start",
            )
        with c2:
            custom_end = st.date_input(
                "Fecha final",
                value=today.date(),
                max_value=today.date(),
                key="garch_custom_end",
            )

    forecast_horizon = st.slider(
        "Horizonte forecast",
        min_value=1,
        max_value=20,
        value=10,
        step=1,
        key="garch_forecast_horizon",
        help="Cantidad de pasos a proyectar en el pronóstico de volatilidad.",
    )

    return_type = st.radio(
        "Tipo de rendimiento",
        ["log", "simple"],
        index=0,
        key="garch_return_type",
        horizontal=True,
    )

    distribution_label = st.selectbox(
        "Distribución de errores",
        ["Normal", "t-Student"],
        index=0,
        key="garch_distribution",
        help=(
            "La normal es el supuesto clásico de errores. "
            "La t-Student permite colas más pesadas y suele ajustar mejor rendimientos financieros extremos."
        ),
    )
    distribution = "t" if distribution_label == "t-Student" else "normal"

    mostrar_diagnostico = st.checkbox(
        "Mostrar diagnóstico del modelo",
        value=True,
        key="garch_show_diag",
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

payload, garch_error = _fetch_garch(
    ticker=ticker,
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
    return_type=return_type,
    mode=modo.lower(),
    forecast_horizon=forecast_horizon,
    distribution=distribution,
)

# 1. Título del módulo actualizado
header_dashboard(
    "Mód. 3: Volatilidad ARCH/GARCH/EGARCH",
    "Modela la volatilidad condicional del activo y compara modelos de heterocedasticidad.",
    modo=modo,
)

# 2. Nota inicial mejorada
if modo == "General":
    nota(
        "Este módulo analiza si la volatilidad del activo cambia en el tiempo. "
        "Los modelos ARCH, GARCH y EGARCH permiten capturar periodos de calma y periodos de alta inestabilidad. "
        "También permite comparar errores normales contra errores t-Student para capturar colas pesadas."
    )
else:
    nota(
        "En modo estadístico se enfatizan la comparación por AIC/BIC, el diagnóstico de residuos, "
        "la volatilidad condicional y el pronóstico de volatilidad futura."
    )

if garch_error:
    st.error(garch_error)
    st.stop()

comparison_df = _format_comparison_table(payload.get("candidate_models", []))
diagnostics_df = _format_diagnostics_table(payload)
forecast_df = _extract_forecast_df(payload)
forecast_final = float(forecast_df.iloc[-1]["volatility"]) if not forecast_df.empty else None

# Extraer valores para KPIs (según el payload del backend)
best_model_name = payload.get("best_model")
best_aic = payload.get("best_model_aic")
best_bic = payload.get("best_model_bic")
best_log_likelihood = _extract_best_log_likelihood(payload)
current_volatility = None
if "conditional_volatility" in payload and payload["conditional_volatility"]:
    # La volatilidad actual es el último valor de la serie
    try:
        current_volatility = float(payload["conditional_volatility"][-1])
    except (IndexError, TypeError, ValueError):
        current_volatility = None

def _format_num(valor, decimales=4):
    if valor is None:
        return "N/D"
    try:
        return f"{float(valor):.{decimales}f}"
    except Exception:
        return str(valor)

def _format_pct(valor):
    if valor is None:
        return "N/D"
    try:
        return f"{float(valor):.2%}"
    except Exception:
        return str(valor)

render_meta_row(
    [
        ("Activo", asset_name),
        ("Ticker", ticker),
        ("País", selected_asset["country"]),
        ("Horizonte", horizonte),
        ("Retorno", return_type),
        ("Distribución", distribution_label),
    ]
)

seccion("KPIs del ajuste")

# 3. KPIs mejorados con help_text
c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    tarjeta_kpi(
        "Mejor modelo",
        str(best_model_name or "N/D"),
        subtexto="Modelo seleccionado según criterio de información.",
        help_text=(
            "El mejor modelo se elige usando criterios como AIC o BIC. "
            "Un menor AIC/BIC indica mejor equilibrio entre ajuste y complejidad."
        ),
    )

with c2:
    tarjeta_kpi(
        "AIC",
        _format_num(best_aic, 4),
        subtexto="Criterio de información de Akaike.",
        help_text=(
            "AIC compara modelos penalizando la complejidad. "
            "Valores más bajos suelen indicar un mejor modelo relativo."
        ),
    )

with c3:
    tarjeta_kpi(
        "BIC",
        _format_num(best_bic, 4),
        subtexto="Criterio bayesiano de información.",
        help_text=(
            "BIC también compara modelos, pero penaliza más la complejidad que AIC. "
            "Se usa para evitar elegir modelos innecesariamente complejos."
        ),
    )

with c4:
    tarjeta_kpi(
        "Log-likelihood",
        _format_num(best_log_likelihood, 4),
        subtexto="Log-verosimilitud del mejor modelo.",
        help_text=(
            "Mide qué tan bien se ajusta el modelo a los datos. "
            "A mayor valor, mejor ajuste, pero sin penalizar la complejidad."
        ),
    )

with c5:
    tarjeta_kpi(
        "Volatilidad actual",
        _format_pct(current_volatility),
        subtexto="Última volatilidad condicional estimada.",
        help_text=(
            "La volatilidad condicional mide el riesgo estimado del activo en cada momento, "
            "considerando que la varianza cambia a través del tiempo."
        ),
    )

with c6:
    tarjeta_kpi(
        "Forecast final",
        f"{forecast_final:.4f}" if forecast_final is not None else "N/D",
        subtexto="Nivel esperado al final del horizonte forecast.",
        help_text="Último valor del pronóstico de volatilidad.",
    )

seccion("Comparación de modelos")

# 7. Agregar tarjeta de comparación antes de la tabla
render_info_card(
    "Comparación de modelos",
    (
        "La comparación entre ARCH, GARCH y EGARCH permite elegir el modelo que mejor representa la dinámica de volatilidad. "
        "ARCH responde más a choques recientes, GARCH captura persistencia y EGARCH puede representar efectos asimétricos. "
        "La distribución t-Student permite errores con colas más pesadas que la normal."
    ),
)

if modo == "General":
    with st.expander("Ver comparación completa de modelos", expanded=False):
        st.dataframe(comparison_df, width="stretch", hide_index=True)
else:
    st.dataframe(comparison_df, width="stretch", hide_index=True)

seccion("Volatilidad y pronóstico")

g1, g2 = st.columns(2, gap="large")

with g1:
    fig_vol, has_multiple_models = _build_conditional_volatility_figure(payload, modo=modo)
    
    # 5. Encabezado mejorado para gráfica de volatilidad
    plot_card_header(
        "Volatilidad condicional estimada",
        (
            "La volatilidad condicional muestra cómo cambia el riesgo estimado del activo a lo largo del tiempo. "
            "Picos altos indican episodios de mayor incertidumbre o estrés."
        ),
        modo=modo,
        caption="Permite identificar periodos de calma y periodos de volatilidad elevada.",
    )
    st.plotly_chart(fig_vol, width="stretch")
    
    # Footer mejorado
    if has_multiple_models:
        plot_card_footer(
            "Se comparan ARCH(1), GARCH(1,1) y EGARCH(1,1). ARCH suele reaccionar con picos más bruscos ante shocks puntuales, mientras GARCH y EGARCH tienden a ofrecer trayectorias más estables para lectura comparativa."
        )
    else:
        plot_card_footer(
            "Los picos de volatilidad no indican necesariamente caída del precio, sino mayor incertidumbre en los rendimientos."
        )

with g2:
    # 6. Encabezado mejorado para forecast
    plot_card_header(
        "Pronóstico de volatilidad",
        (
            "El forecast proyecta la volatilidad esperada para los próximos periodos usando el modelo seleccionado."
        ),
        modo=modo,
        caption="Sirve para anticipar si el riesgo estimado tiende a mantenerse, subir o bajar en el corto plazo.",
    )
    forecast_df = pd.DataFrame(payload.get("forecast", []))

    fig_forecast = _build_forecast_figure(
        forecast_df,
        modo=modo,
        clean_view=False,
    )
    st.plotly_chart(fig_forecast, width="stretch")
    # Footer mejorado para forecast
    plot_card_footer(
        _forecast_message(payload)
    )

if mostrar_diagnostico:
    seccion("Diagnóstico")
    
    # 4. Tarjeta de lectura del módulo (interpretación general)
    compact_help_card(
        "Lectura del módulo",
        (
            "Los modelos ARCH/GARCH permiten estudiar volatilidad agrupada: periodos tranquilos tienden a estar seguidos "
            "por periodos tranquilos, y periodos turbulentos por nuevos episodios de alta volatilidad. "
            "ARCH captura choques recientes, GARCH incorpora persistencia de la volatilidad y EGARCH permite capturar "
            "asimetrías, es decir, que malas noticias y buenas noticias puedan afectar de forma distinta el riesgo. "
            "Con errores t-Student se permite mayor probabilidad en las colas frente a una normal."
        ),
        caption="Resumen conceptual del comportamiento de la volatilidad condicional.",
    )

    plot_card_header(
        "Diagnóstico del modelo",
        "Medidas clave del mejor ajuste, útiles para interpretación y sustentación técnica.",
        modo=modo,
        caption="La tabla resume el ajuste y la caja inferior te ayuda a defenderlo metodológicamente.",
    )

    st.dataframe(diagnostics_df, width="stretch", hide_index=True)

    compact_help_card(
        "Cómo hacer el diagnóstico",
        _diagnostic_guide(payload),
        caption="Pasa el cursor sobre el signo de ayuda para ver la guía metodológica.",
    )