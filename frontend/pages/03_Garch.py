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


def _format_diagnostics_table(payload: dict) -> pd.DataFrame:
    rows = [
        {"Métrica": "Observaciones", "Valor": payload.get("observations")},
        {"Métrica": "Mejor modelo", "Valor": payload.get("best_model")},
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


def _render_pretty_diagnostics_table(df: pd.DataFrame):
    if df.empty:
        st.warning("No hay diagnóstico disponible.")
        return

    rows_html = "".join(
        [
            f"""
            <tr>
                <td style="padding:0.82rem 0.9rem;border-bottom:1px solid rgba(148,163,184,0.14);font-weight:700;color:var(--text-main);">
                    {row["Métrica"]}
                </td>
                <td style="padding:0.82rem 0.9rem;border-bottom:1px solid rgba(148,163,184,0.14);color:var(--text-soft);font-weight:600;">
                    {row["Valor"]}
                </td>
            </tr>
            """
            for _, row in df.iterrows()
        ]
    )

    st.markdown(
        f"""
        <div style="
            background:linear-gradient(180deg,#ffffff 0%, var(--panel-bg-2) 100%);
            border:1px solid var(--border-soft);
            border-radius:20px;
            overflow:hidden;
            box-shadow:var(--shadow-main);
            margin-top:0.35rem;
        ">
            <div style="
                display:grid;
                grid-template-columns: 1.15fr 1fr;
                background:rgba(15,23,42,0.96);
                color:#F8FAFC;
                font-weight:800;
                letter-spacing:0.04em;
                text-transform:uppercase;
                font-size:0.80rem;
            ">
                <div style="padding:0.9rem 0.9rem;">Métrica</div>
                <div style="padding:0.9rem 0.9rem;">Valor</div>
            </div>
            <table style="width:100%;border-collapse:collapse;">
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _build_conditional_volatility_figure(payload: dict, modo: str) -> go.Figure:
    cond_vol = payload.get("conditional_volatility", []) or []
    fig = go.Figure()

    if cond_vol:
        x = list(range(1, len(cond_vol) + 1))
        fig.add_trace(
            go.Scatter(
                x=x,
                y=cond_vol,
                mode="lines",
                name=str(payload.get("best_model", "Volatilidad")),
                line=dict(width=2.4),
            )
        )

    return style_plotly_figure(
        fig,
        modo=modo,
        title="Volatilidad condicional estimada",
        xaxis_title="Observación",
        yaxis_title="Volatilidad",
        show_xgrid=True,
        show_ygrid=True,
    )


def _build_forecast_figure(payload: dict, modo: str) -> go.Figure:
    forecast = payload.get("forecast", []) or []
    fig = go.Figure()

    if forecast:
        forecast_df = pd.DataFrame(forecast)

        if "step" not in forecast_df.columns:
            forecast_df["step"] = range(1, len(forecast_df) + 1)

        if "volatility" in forecast_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=forecast_df["step"],
                    y=forecast_df["volatility"],
                    mode="lines+markers",
                    name="Pronóstico",
                    line=dict(width=2.4),
                )
            )

    return style_plotly_figure(
        fig,
        modo=modo,
        title="Pronóstico de volatilidad",
        xaxis_title="Horizonte",
        yaxis_title="Volatilidad",
        show_xgrid=True,
        show_ygrid=True,
    )


def _forecast_message(payload: dict) -> str:
    forecast = payload.get("forecast", []) or []
    eff_h = payload.get("effective_forecast_horizon")

    if not forecast:
        return "El backend no devolvió una trayectoria de forecast utilizable."

    if len(forecast) == 1 or eff_h == 1:
        point = forecast[0].get("volatility")
        point_text = f"{float(point):.4f}" if point is not None else "N/D"
        return (
            f"El backend entregó un forecast efectivo de un solo paso. "
            f"Por eso el gráfico muestra un nivel puntual y no una trayectoria completa. "
            f"La volatilidad esperada inmediata es {point_text}."
        )

    first_v = forecast[0].get("volatility")
    last_v = forecast[-1].get("volatility")
    first_t = f"{float(first_v):.4f}" if first_v is not None else "N/D"
    last_t = f"{float(last_v):.4f}" if last_v is not None else "N/D"

    return (
        f"El pronóstico cubre {len(forecast)} pasos. "
        f"Parte desde {first_t} y termina en {last_t}. "
        f"Úsalo para evaluar si la volatilidad tendería a subir, bajar o estabilizarse."
    )


def _diagnostic_guide(payload: dict) -> str:
    model = str(payload.get("best_model", "N/D"))
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
        f"Para diagnosticar el ajuste, primero identifica el modelo ganador: {model}. "
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
)

header_dashboard(
    "Módulo 3 - Modelos ARCH / GARCH / EGARCH",
    "Compara especificaciones de volatilidad condicional y revisa el pronóstico del mejor modelo seleccionado por backend",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo compara variantes ARCH/GARCH/EGARCH para identificar cuál describe mejor la dinámica reciente de volatilidad del activo."
    )
else:
    nota(
        "En modo estadístico se enfatiza la comparación técnica entre modelos, la volatilidad condicional estimada, el pronóstico y el diagnóstico de residuos."
    )

if garch_error:
    st.error(garch_error)
    st.stop()

comparison_df = _format_comparison_table(payload.get("candidate_models", []))
diagnostics_df = _format_diagnostics_table(payload)
forecast_list = payload.get("forecast", []) or []
forecast_final = forecast_list[-1]["volatility"] if forecast_list and "volatility" in forecast_list[-1] else None

render_meta_row(
    [
        ("Activo", asset_name),
        ("Ticker", ticker),
        ("País", selected_asset["country"]),
        ("Horizonte", horizonte),
        ("Retorno", return_type),
    ]
)

seccion("KPIs del ajuste")

c1, c2, c3, c4 = st.columns(4)

with c1:
    tarjeta_kpi(
        "Activo",
        asset_name,
        subtexto="Activo usado como base del ajuste.",
        help_text="Ticker y nombre del activo seleccionado.",
    )

with c2:
    tarjeta_kpi(
        "Modelos comparados",
        str(len(comparison_df)),
        subtexto="Cantidad de variantes ARCH/GARCH evaluadas.",
        help_text="Número de especificaciones candidatas devueltas por el backend.",
    )

with c3:
    tarjeta_kpi(
        "Mejor modelo",
        str(payload.get("best_model", "N/D")),
        subtexto="Especificación con mejor desempeño comparativo.",
        help_text="Modelo con menor AIC dentro de las alternativas evaluadas.",
    )

with c4:
    tarjeta_kpi(
        "Forecast final",
        f"{float(forecast_final):.4f}" if forecast_final is not None else "N/D",
        subtexto="Nivel esperado al final del horizonte forecast.",
        help_text="Último valor del pronóstico de volatilidad.",
    )

c5, c6 = st.columns(2)

with c5:
    tarjeta_kpi(
        "Observaciones",
        str(payload.get("observations", "N/D")),
        subtexto="Datos efectivos usados en el ajuste.",
        help_text="Tamaño muestral empleado por el modelo.",
    )

with c6:
    tarjeta_kpi(
        "JB p-value",
        f"{float(payload.get('residuals_jarque_bera_p_value')):.6f}" if payload.get("residuals_jarque_bera_p_value") is not None else "N/D",
        subtexto="Normalidad de residuos estandarizados.",
        help_text="P-value de Jarque-Bera sobre residuos del mejor modelo.",
    )

plot_card_footer(_diagnostic_guide(payload))

seccion("Comparación de modelos")

if modo == "General":
    with st.expander("Ver comparación completa de modelos", expanded=False):
        st.dataframe(comparison_df, width="stretch")
else:
    st.dataframe(comparison_df, width="stretch")

seccion("Volatilidad y pronóstico")

g1, g2 = st.columns(2, gap="large")

with g1:
    plot_card_header(
        "Volatilidad condicional estimada",
        "El backend actual devuelve la serie del mejor modelo seleccionado, no las tres trayectorias por separado.",
        modo=modo,
        caption="Aquí se observa la volatilidad condicional del modelo ganador. Para comparar trayectorias ARCH, GARCH y EGARCH en una sola gráfica habría que ampliar el endpoint.",
    )
    fig_vol = _build_conditional_volatility_figure(payload, modo=modo)
    st.plotly_chart(fig_vol, width="stretch")
    plot_card_footer(
        "Esta vista corresponde únicamente al mejor modelo devuelto por backend. No es una comparación simultánea entre modelos."
    )

with g2:
    plot_card_header(
        "Forecast de volatilidad",
        "Pronóstico devuelto por el modelo seleccionado por backend.",
        modo=modo,
        caption="Si el backend retorna un horizonte efectivo de un paso, el gráfico mostrará un único punto.",
    )
    fig_forecast = _build_forecast_figure(payload, modo=modo)
    st.plotly_chart(fig_forecast, width="stretch")
    plot_card_footer(_forecast_message(payload))

if mostrar_diagnostico:
    seccion("Diagnóstico")

    plot_card_header(
        "Diagnóstico del modelo",
        "Medidas clave del mejor ajuste, útiles para interpretación y sustentación técnica.",
        modo=modo,
        caption="La tabla resume el ajuste y la caja inferior te dice cómo defenderlo metodológicamente.",
    )

    _render_pretty_diagnostics_table(diagnostics_df)

    st.markdown("")
    render_info_card(
        "Cómo hacer el diagnóstico",
        _diagnostic_guide(payload),
    )