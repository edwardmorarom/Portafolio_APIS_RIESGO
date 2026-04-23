from __future__ import annotations

import math
import pandas as pd
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


BASE_PORTFOLIO = [
    {"name": "Seven & i Holdings", "ticker": "3382.T", "country": "JP"},
    {"name": "Alimentation Couche-Tard", "ticker": "ATD.TO", "country": "CA"},
    {"name": "FEMSA", "ticker": "FEMSAUBD.MX", "country": "MX"},
    {"name": "BP", "ticker": "BP.L", "country": "UK"},
    {"name": "Carrefour", "ticker": "CA.PA", "country": "FR"},
]


def _fetch_help() -> tuple[dict[str, dict], str | None]:
    client = get_api_client()
    try:
        help_payload = client.get_help_catalog()
        help_map = {item["key"]: item for item in help_payload.get("items", [])}
        return help_map, None
    except ApiClientError:
        return {}, None


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


def _normalize_weights(raw_weights: list[float]) -> list[float]:
    total = sum(raw_weights)
    if total <= 0:
        return [1 / len(raw_weights)] * len(raw_weights)
    return [w / total for w in raw_weights]


def _portfolio_table(weights: list[float]) -> pd.DataFrame:
    rows = []
    for asset, weight in zip(BASE_PORTFOLIO, weights):
        rows.append(
            {
                "Activo": asset["name"],
                "Ticker": asset["ticker"],
                "Peso": f"{weight:.2%}",
            }
        )
    return pd.DataFrame(rows)


def _build_var_payload(
    start: str,
    end: str,
    weights: list[float],
    confidence_level: float,
    base_currency: str,
    portfolio_value: float,
    mc_n_sims: int,
) -> dict:
    return {
        "tickers": [asset["ticker"] for asset in BASE_PORTFOLIO],
        "weights": weights,
        "start": start,
        "end": end,
        "confidence_level": confidence_level,
        "base_currency": base_currency,
        "portfolio_value": portfolio_value,
        "mc_n_sims": mc_n_sims,
    }


def _fetch_var(payload: dict) -> tuple[dict, str | None]:
    client = get_api_client()
    try:
        response = client.post_var_risk(payload)
        if response is None:
            return {}, "El endpoint VaR/CVaR respondió vacío."
        if not isinstance(response, dict):
            return {}, f"Respuesta VaR/CVaR no válida: {type(response).__name__}"
        return response, None
    except ApiClientError as exc:
        return {}, exc.message
    except Exception as exc:
        return {}, f"Error inesperado consultando VaR/CVaR: {exc}"


def _pick_value(payload: dict | None, *keys):
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _extract_method_block(payload: dict, method_name: str) -> dict:
    aliases = {
        "historical": ["historical", "hist", "historico"],
        "parametric": ["parametric", "gaussian", "parametrico"],
        "monte_carlo": ["monte_carlo", "mc", "montecarlo"],
    }

    for alias in aliases.get(method_name, [method_name]):
        if isinstance(payload.get(alias), dict):
            return payload[alias]

    block = {}
    prefixes = aliases.get(method_name, [method_name])
    for prefix in prefixes:
        for key, value in payload.items():
            if key.startswith(f"{prefix}_"):
                block[key[len(prefix) + 1 :]] = value
    return block


def _method_metric(payload: dict, method_name: str, *keys):
    block = _extract_method_block(payload, method_name)

    for key in keys:
        if key in block and block[key] is not None:
            return block[key]

    top_keys = []
    for key in keys:
        top_keys.extend(
            [
                f"{method_name}_{key}",
                f"{method_name.replace('_', '')}_{key}",
            ]
        )

    return _pick_value(payload, *top_keys)


def _extract_distribution(payload: dict) -> pd.Series:
    for key in [
        "portfolio_returns",
        "returns_distribution",
        "distribution",
        "simulated_returns",
        "portfolio_distribution",
    ]:
        val = payload.get(key)
        if isinstance(val, list) and val:
            s = pd.to_numeric(pd.Series(val), errors="coerce").dropna()
            if not s.empty:
                return s

    samples = []
    for method_name in ["historical", "parametric", "monte_carlo"]:
        block = _extract_method_block(payload, method_name)
        for key in ["samples", "returns", "distribution", "simulated_returns"]:
            val = block.get(key)
            if isinstance(val, list) and val:
                s = pd.to_numeric(pd.Series(val), errors="coerce").dropna()
                if not s.empty:
                    samples.append(s)

    if samples:
        return samples[0]

    return pd.Series(dtype=float)


def _extract_backtest(payload: dict) -> dict:
    for key in ["backtesting", "kupiec", "kupiec_test", "backtest"]:
        val = payload.get(key)
        if isinstance(val, dict):
            return val
    return {}


def _format_pct(x) -> str:
    if x is None:
        return "N/D"
    try:
        return f"{float(x):.2%}"
    except Exception:
        return str(x)


def _format_num(x, ndigits: int = 4) -> str:
    if x is None:
        return "N/D"
    try:
        return f"{float(x):.{ndigits}f}"
    except Exception:
        return str(x)


def _comparison_table(payload: dict) -> pd.DataFrame:
    rows = []
    for method_name, label in [
        ("parametric", "Paramétrico"),
        ("historical", "Histórico"),
        ("monte_carlo", "Monte Carlo"),
    ]:
        rows.append(
            {
                "método": label,
                "VaR_diario": _method_metric(payload, method_name, "var_daily", "var"),
                "CVaR_diario": _method_metric(payload, method_name, "cvar_daily", "cvar"),
                "VaR_anualizado": _method_metric(payload, method_name, "var_annualized"),
                "CVaR_anualizado": _method_metric(payload, method_name, "cvar_annualized"),
            }
        )
    df = pd.DataFrame(rows)

    for col in ["VaR_diario", "CVaR_diario", "VaR_anualizado", "CVaR_anualizado"]:
        df[col] = df[col].apply(_format_num)
    return df


def _interpret_main_risk(payload: dict, confidence_level: float) -> str:
    var_hist = _method_metric(payload, "historical", "var_daily", "var")
    cvar_hist = _method_metric(payload, "historical", "cvar_daily", "cvar")
    var_param = _method_metric(payload, "parametric", "var_daily", "var")
    var_mc = _method_metric(payload, "monte_carlo", "var_daily", "var")

    ch = int(confidence_level * 100)

    return (
        f"Con {ch}% de confianza, el VaR histórico diario es {_format_pct(var_hist)} y el CVaR histórico diario asciende a "
        f"{_format_pct(cvar_hist)}. El VaR paramétrico se estima en {_format_pct(var_param)} y el VaR Monte Carlo en {_format_pct(var_mc)}."
    )


def _build_distribution_figure(
    returns_s: pd.Series,
    payload: dict,
    modo: str,
    show_hist: bool,
    show_var: bool,
    show_cvar: bool,
    clean_view: bool,
) -> go.Figure:
    fig = go.Figure()

    if not returns_s.empty:
        fig.add_trace(
            go.Histogram(
                x=returns_s,
                name="Rendimientos",
                opacity=0.78,
                nbinsx=35,
            )
        )

    line_specs = []

    if show_var:
        for method_name, label, color in [
            ("parametric", "VaR Paramétrico", "#1D4ED8"),
            ("historical", "VaR Histórico", "#0F766E"),
            ("monte_carlo", "VaR Monte Carlo", "#7C3AED"),
        ]:
            value = _method_metric(payload, method_name, "var_daily", "var")
            if value is not None:
                fig.add_vline(
                    x=float(value),
                    line_dash="dash",
                    line_width=2.2,
                    line_color=color,
                )
                line_specs.append((label, color, float(value)))

    if show_cvar:
        for method_name, label, color in [
            ("parametric", "CVaR Paramétrico", "#DC2626"),
            ("historical", "CVaR Histórico", "#D97706"),
            ("monte_carlo", "CVaR Monte Carlo", "#BE185D"),
        ]:
            value = _method_metric(payload, method_name, "cvar_daily", "cvar")
            if value is not None:
                fig.add_vline(
                    x=float(value),
                    line_dash="dot",
                    line_width=2.2,
                    line_color=color,
                )
                line_specs.append((label, color, float(value)))

    for trace in fig.data:
        if str(getattr(trace, "name", "")).lower() == "rendimientos":
            trace.visible = True if show_hist else "legendonly"

    fig = style_plotly_figure(
        fig,
        modo=modo,
        title="Distribución de rendimientos y riesgo extremo",
        xaxis_title="Rendimiento",
        yaxis_title="Frecuencia",
        show_xgrid=not clean_view,
        show_ygrid=not clean_view,
    )

    # Fondo del área del gráfico más azul
    fig.update_layout(
        plot_bgcolor="#E8F0FF" if modo == "General" else "#F8EAF1",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=24, r=24, t=72, b=24),
    )

    # Histograma con azul más visible
    fig.update_traces(
        selector=dict(type="histogram"),
        marker=dict(
            color="rgba(59, 130, 246, 0.55)",
            line=dict(color="rgba(29, 78, 216, 0.55)", width=0.6),
        ),
    )

    if line_specs:
        var_specs = [item for item in line_specs if item[0].startswith("VaR")]
        cvar_specs = [item for item in line_specs if item[0].startswith("CVaR")]

        legend_items = [("VaR", var_specs), ("CVaR", cvar_specs)]

        base_x0 = 0.01
        base_x1 = 0.29
        top_y = 0.99
        row_gap = 0.052
        section_gap = 0.03

        current_y = top_y

        # fondo del panel
        total_rows = sum(len(items) for _, items in legend_items) + len([1 for _, items in legend_items if items])
        panel_height = total_rows * row_gap + section_gap
        fig.add_shape(
            type="rect",
            xref="paper",
            yref="paper",
            x0=base_x0,
            x1=base_x1,
            y0=max(0.02, top_y - panel_height),
            y1=1.0,
            line=dict(color="rgba(148,163,184,0.35)", width=1),
            fillcolor="rgba(255,255,255,0.88)",
            layer="below",
        )

        for section_title, items in legend_items:
            if not items:
                continue

            fig.add_annotation(
                xref="paper",
                yref="paper",
                x=0.02,
                y=current_y,
                xanchor="left",
                yanchor="top",
                showarrow=False,
                text=f"<b>{section_title}</b>",
                font=dict(size=11, color="#0F172A"),
            )
            current_y -= row_gap

            for label, color, value in items:
                fig.add_shape(
                    type="line",
                    xref="paper",
                    yref="paper",
                    x0=0.02,
                    x1=0.06,
                    y0=current_y,
                    y1=current_y,
                    line=dict(color=color, width=3),
                )

                fig.add_annotation(
                    xref="paper",
                    yref="paper",
                    x=0.065,
                    y=current_y,
                    xanchor="left",
                    yanchor="middle",
                    showarrow=False,
                    text=f"{label}: {value:.2%}",
                    font=dict(size=10.5, color="#0F172A"),
                )

                current_y -= row_gap

            current_y -= section_gap

    return fig


help_map, _ = _fetch_help()

modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros de Riesgo Extremo",
    filtros_expanded=False,
)

today = pd.Timestamp.today().normalize()

with filtros_sidebar:
    horizonte = st.selectbox(
        "Horizonte de análisis",
        ["1 mes", "Trimestre", "Semestre", "1 año", "3 años", "5 años", "Personalizado"],
        index=3,
        key="var_horizonte_backend",
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
                key="var_custom_start",
            )
        with c2:
            custom_end = st.date_input(
                "Fecha final",
                value=today.date(),
                max_value=today.date(),
                key="var_custom_end",
            )

    confidence_level = st.selectbox(
        "Nivel de confianza",
        [0.90, 0.95, 0.99],
        index=1,
        key="var_confidence",
        format_func=lambda x: f"{int(x*100)}%",
    )

    base_currency = st.selectbox(
        "Moneda base",
        ["USD", "EUR", "COP"],
        index=0,
        key="var_base_currency",
    )

    portfolio_value = st.number_input(
        "Valor portafolio",
        min_value=1000.0,
        value=100000.0,
        step=1000.0,
        key="var_portfolio_value",
    )

    mc_n_sims = st.slider(
        "Simulaciones Monte Carlo",
        min_value=500,
        max_value=20000,
        value=5000,
        step=500,
        key="var_mc_sims",
    )

    st.markdown("**Pesos del portafolio**")
    raw_weights = []
    for asset in BASE_PORTFOLIO:
        w = st.slider(
            f"{asset['ticker']}",
            min_value=0.0,
            max_value=1.0,
            value=0.20,
            step=0.01,
            key=f"weight_{asset['ticker']}",
        )
        raw_weights.append(w)

weights = _normalize_weights(raw_weights)
start_date, end_date = _resolve_dates(
    horizonte=horizonte,
    default_end=today,
    custom_start=pd.Timestamp(custom_start) if custom_start is not None else None,
    custom_end=pd.Timestamp(custom_end) if custom_end is not None else None,
)

if start_date >= end_date:
    st.error("La fecha inicial debe ser menor que la fecha final.")
    st.stop()

request_payload = _build_var_payload(
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
    weights=weights,
    confidence_level=confidence_level,
    base_currency=base_currency,
    portfolio_value=portfolio_value,
    mc_n_sims=mc_n_sims,
)

payload, risk_error = _fetch_var(request_payload)

header_dashboard(
    "Módulo 5 - VaR y CVaR",
    "Evalúa el riesgo extremo del portafolio mediante VaR y CVaR bajo distintos enfoques de estimación",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo traduce el riesgo extremo del portafolio en pérdidas umbral y pérdidas medias severas bajo escenarios adversos."
    )
else:
    nota(
        "En modo estadístico se enfatiza la comparación entre métodos, la distribución de rendimientos extremos y el backtesting de consistencia."
    )

if risk_error:
    st.error(risk_error)
    st.stop()

if not isinstance(payload, dict) or not payload:
    st.error("No se recibieron datos válidos del endpoint VaR/CVaR.")
    st.stop()

returns_s = _extract_distribution(payload)
comparison_df = _comparison_table(payload)
backtest = _extract_backtest(payload)
portfolio_df = _portfolio_table(weights)

render_meta_row(
    [
        ("Confianza", f"{int(confidence_level*100)}%"),
        ("Moneda base", base_currency),
        ("Horizonte", horizonte),
        ("Activos", str(len(BASE_PORTFOLIO))),
    ]
)

tab1, tab2, tab3 = st.tabs(
    ["Resumen y KPIs", "Distribución de riesgo", "Comparación y backtesting"]
)

with tab1:
    seccion("Resumen del módulo")
    render_info_card(
        "Lectura general",
        f"Se estima cuánto podría perder el portafolio con un nivel de confianza del {int(confidence_level*100)}%. El VaR representa una pérdida umbral y el CVaR resume la severidad promedio de la cola extrema.",
    )

    seccion("Portafolio analizado")
    render_info_card(
        "Pesos normalizados",
        "Los pesos del portafolio se ajustan desde el panel lateral y se normalizan automáticamente para que sumen 100%.",
    )
    st.dataframe(portfolio_df, width="stretch", hide_index=True)

    seccion("KPIs de riesgo")

    var_hist = _method_metric(payload, "historical", "var_daily", "var")
    cvar_hist = _method_metric(payload, "historical", "cvar_daily", "cvar")
    var_param = _method_metric(payload, "parametric", "var_daily", "var")
    var_mc = _method_metric(payload, "monte_carlo", "var_daily", "var")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tarjeta_kpi(
            "VaR histórico 95%",
            _format_pct(var_hist),
            subtexto="Umbral de pérdida diaria bajo la distribución observada.",
            help_text="Percentil de cola izquierda estimado históricamente.",
        )

    with c2:
        tarjeta_kpi(
            "CVaR histórico 95%",
            _format_pct(cvar_hist),
            subtexto="Severidad media una vez se supera el VaR.",
            help_text="Promedio de pérdidas en la cola extrema.",
        )

    with c3:
        tarjeta_kpi(
            "VaR paramétrico",
            _format_pct(var_param),
            subtexto="Cálculo cerrado bajo media y desviación estándar.",
            help_text="Aproximación gaussiana del riesgo extremo.",
        )

    with c4:
        tarjeta_kpi(
            "VaR Monte Carlo",
            _format_pct(var_mc),
            subtexto="Riesgo extremo aproximado a partir de simulación.",
            help_text="Estimación basada en trayectorias simuladas.",
        )

    plot_card_footer(_interpret_main_risk(payload, confidence_level))

with tab2:
    seccion("Distribución y riesgo extremo")

    plot_card_header(
        "Distribución de rendimientos del portafolio",
        "Histograma de rendimientos con líneas de referencia para VaR y CVaR.",
        modo=modo,
        caption="La leyenda lateral izquierda resume cada umbral de riesgo con colores distintos para evitar superposición visual.",
)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        show_hist = st.checkbox("Histograma", value=True, key="var_show_hist")
    with c2:
        show_var = st.checkbox("Líneas VaR", value=True, key="var_show_var")
    with c3:
        show_cvar = st.checkbox("Líneas CVaR", value=True, key="var_show_cvar")
    with c4:
        clean_view = st.checkbox("Vista limpia", value=False, key="var_clean_view")

    fig_dist = _build_distribution_figure(
        returns_s=returns_s,
        payload=payload,
        modo=modo,
        show_hist=show_hist,
        show_var=show_var,
        show_cvar=show_cvar,
        clean_view=clean_view,
    )
    st.plotly_chart(fig_dist, width="stretch")

    if returns_s.empty:
        plot_card_footer(
            "El backend no devolvió una distribución explícita de rendimientos para graficar; solo se muestran las métricas disponibles."
        )
    else:
        plot_card_footer(
            "La distribución permite ubicar visualmente dónde caen los umbrales VaR y CVaR frente a los rendimientos del portafolio."
        )

with tab3:
    seccion("Comparación VaR / CVaR")

    if modo == "General":
        with st.expander("Ver tabla comparativa de VaR y CVaR", expanded=False):
            st.dataframe(comparison_df, width="stretch", hide_index=True)
    else:
        st.dataframe(comparison_df, width="stretch", hide_index=True)

    seccion("Interpretación")
    render_info_card(
        "Lectura técnica",
        _interpret_main_risk(payload, confidence_level),
    )

    seccion("Backtesting VaR - Test de Kupiec")

    violations = _pick_value(
        backtest,
        "violations",
        "n_violations",
        "exceptions",
    )
    observed_rate = _pick_value(
        backtest,
        "observed_rate",
        "observed_exception_rate",
        "hit_rate",
    )
    expected_rate = _pick_value(
        backtest,
        "expected_rate",
        "expected_exception_rate",
        "alpha",
    )
    kupiec_p = _pick_value(
        backtest,
        "p_value",
        "kupiec_p_value",
    )
    kupiec_conclusion = _pick_value(
        backtest,
        "conclusion",
        "decision",
    )

    k1, k2, k3 = st.columns(3)
    with k1:
        tarjeta_kpi(
            "Violaciones",
            _format_num(violations, 0),
            subtexto="Excesos observados frente al umbral estimado.",
            help_text="Número de veces en que la pérdida superó el VaR.",
        )
    with k2:
        tarjeta_kpi(
            "Observadas (%)",
            _format_pct(observed_rate),
            subtexto="Tasa real registrada en la muestra.",
            help_text="Frecuencia observada de violaciones.",
        )
    with k3:
        tarjeta_kpi(
            "Esperadas (%)",
            _format_pct(expected_rate),
            subtexto="Tasa teórica coherente con el nivel de confianza.",
            help_text="Frecuencia esperada si el VaR está bien calibrado.",
        )

    if kupiec_p is not None:
        plot_card_footer(
            f"Se observaron {_format_num(violations, 0)} violaciones del VaR. La tasa observada fue {_format_pct(observed_rate)} frente a una tasa esperada de {_format_pct(expected_rate)}. El p-valor del test es {_format_num(kupiec_p, 4)}."
        )

    if kupiec_conclusion is not None:
        render_info_card(
            "Conclusión de Kupiec",
            str(kupiec_conclusion),
        )
    else:
        render_info_card(
            "Conclusión de Kupiec",
            "El backend no devolvió una conclusión textual del backtesting para este cálculo.",
        )