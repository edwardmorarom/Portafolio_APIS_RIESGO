from __future__ import annotations

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


PORTFOLIO_ASSETS = [
    {"name": "Seven & i Holdings", "ticker": "3382.T", "country": "JP"},
    {"name": "Alimentation Couche-Tard", "ticker": "ATD.TO", "country": "CA"},
    {"name": "FEMSA", "ticker": "FEMSAUBD.MX", "country": "MX"},
    {"name": "BP", "ticker": "BP.L", "country": "UK"},
    {"name": "Carrefour", "ticker": "CA.PA", "country": "FR"},
]


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


def _weights_editor(sidebar_container, key_prefix: str) -> tuple[list[float], float]:
    with sidebar_container:
        st.markdown("**Pesos del portafolio (%)**")
        weights_pct: list[float] = []
        for asset in PORTFOLIO_ASSETS:
            value = st.number_input(
                asset["ticker"],
                min_value=0.0,
                max_value=100.0,
                value=20.0,
                step=1.0,
                key=f"{key_prefix}_{asset['ticker']}",
                format="%.2f",
            )
            weights_pct.append(float(value))

        total_pct = float(sum(weights_pct))
        st.caption(f"Total asignado: {total_pct:.2f}%")

        if total_pct > 100.0 + 1e-6:
            st.error("Los pesos no pueden superar 100%.")
        elif abs(total_pct - 100.0) > 1e-6:
            st.warning("Para calcular VaR/CVaR, los pesos deben sumar exactamente 100%.")

    return [w / 100.0 for w in weights_pct], total_pct


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


def _fetch_var(
    tickers: list[str],
    weights: list[float],
    start: str,
    end: str,
    alpha: float,
    n_sim: int,
    return_type: str = "log",
) -> tuple[dict, str | None]:
    client = get_api_client()

    payload = {
        "tickers": tickers,
        "weights": weights,
        "start": start,
        "end": end,
        "alpha": alpha,
        "n_sim": n_sim,
        "return_type": return_type,
    }

    try:
        response = client.post_var_risk(payload)
        if response is None:
            return {}, "El endpoint de riesgo respondió vacío."
        if not isinstance(response, dict):
            return {}, f"Respuesta de riesgo no válida: {type(response).__name__}"
        return response, None
    except ApiClientError as exc:
        return {}, exc.message
    except Exception as exc:
        return {}, f"Error inesperado consultando VaR/CVaR: {exc}"


def _method_metric(payload: dict, method_key: str, *metric_names):
    method = payload.get(method_key)
    if not isinstance(method, dict):
        return None
    for name in metric_names:
        if name in method and method[name] is not None:
            return method[name]
    return None


def _extract_distribution_series(payload: dict) -> pd.Series:
    for key in ["portfolio_returns", "returns_distribution", "distribution", "simulated_returns"]:
        val = payload.get(key)
        if isinstance(val, list) and val:
            s = pd.to_numeric(pd.Series(val), errors="coerce").dropna()
            if not s.empty:
                return s
    return pd.Series(dtype=float)


def _extract_kupiec(payload: dict) -> dict:
    for key in ["kupiec_test", "kupiec", "kupiec_backtest", "backtesting"]:
        val = payload.get(key)
        if isinstance(val, dict):
            return val
    return {}


def _comparison_table(payload: dict) -> pd.DataFrame:
    rows = []
    for key, label in [
        ("historical", "Histórico"),
        ("parametric", "Paramétrico"),
        ("monte_carlo", "Monte Carlo"),
    ]:
        method = payload.get(key, {})
        if not isinstance(method, dict):
            continue
        rows.append(
            {
                "Método": label,
                "VaR diario": _format_pct(method.get("var_daily")),
                "CVaR diario": _format_pct(method.get("cvar_daily")),
                "VaR anualizado": _format_pct(method.get("var_annualized")),
                "CVaR anualizado": _format_pct(method.get("cvar_annualized")),
            }
        )
    return pd.DataFrame(rows)


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

    fig.update_layout(
        plot_bgcolor="#E8F0FF" if modo == "General" else "#F8EAF1",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=24, r=24, t=72, b=24),
    )

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

    alpha_label = st.selectbox("Nivel de confianza", ["90%", "95%", "99%"], index=1, key="var_alpha_label")
    alpha_map = {"90%": 0.90, "95%": 0.95, "99%": 0.99}
    alpha = alpha_map[alpha_label]

    base_currency = st.selectbox("Moneda base", ["USD", "EUR", "COP"], index=0, key="var_base_currency")

    portfolio_value = st.number_input(
        "Valor portafolio",
        min_value=1000.0,
        max_value=100000000.0,
        value=100000.0,
        step=1000.0,
        key="var_portfolio_value",
        format="%.2f",
    )

    mc_n_sims = st.slider(
        "Simulaciones Monte Carlo",
        min_value=10000,
        max_value=50000,
        value=10000,
        step=1000,
        key="var_mc_sims",
    )

    weights_decimals, total_pct = _weights_editor(filtros_sidebar, "var_weight")

start_date, end_date = _resolve_dates(
    horizonte=horizonte,
    default_end=today,
    custom_start=pd.Timestamp(custom_start) if custom_start is not None else None,
    custom_end=pd.Timestamp(custom_end) if custom_end is not None else None,
)

if start_date >= end_date:
    st.error("La fecha inicial debe ser menor que la fecha final.")
    st.stop()

payload = {}
risk_error = None
if abs(total_pct - 100.0) <= 1e-6:
    payload, risk_error = _fetch_var(
        tickers=[a["ticker"] for a in PORTFOLIO_ASSETS],
        weights=weights_decimals,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        alpha=alpha,
        n_sim=mc_n_sims,
        return_type="log",
    )

header_dashboard(
    "Mód. 5: VaR y CVaR",
    "Cuantificar la pérdida potencial del portafolio.",
    modo=modo,
)

if modo == "General":
    nota(
        "Incluye VaR paramétrico, VaR histórico, VaR Monte Carlo, Expected Shortfall y backtesting de Kupiec."
    )
else:
    nota(
        "En modo estadístico se enfatiza la comparación de métodos, la distribución de rendimientos y el backtesting del VaR."
    )

if abs(total_pct - 100.0) > 1e-6:
    st.error("Los pesos del portafolio deben sumar exactamente 100% para calcular VaR/CVaR.")
    st.stop()

if risk_error:
    st.error(risk_error)
    st.stop()

returns_s = _extract_distribution_series(payload)
kupiec = _extract_kupiec(payload)
comparison_df = _comparison_table(payload)

render_meta_row(
    [
        ("Confianza", alpha_label),
        ("Moneda", base_currency),
        ("Portafolio", f"{portfolio_value:,.2f}".replace(",", ".")),
        ("Simulaciones", f"{mc_n_sims:,}".replace(",", ".")),
        ("Horizonte", horizonte),
    ]
)

tab1, tab2, tab3 = st.tabs(["Resumen y KPIs", "Distribución de riesgo", "Comparación y backtesting"])

with tab1:
    seccion("Resumen VaR / CVaR")

    confidence_label = f"{int(alpha * 100)}%"

    var_hist = _method_metric(payload, "historical", "var_daily", "var")
    cvar_hist = _method_metric(payload, "historical", "cvar_daily", "cvar")
    var_param = _method_metric(payload, "parametric", "var_daily", "var")
    cvar_param = _method_metric(payload, "parametric", "cvar_daily", "cvar")
    var_mc = _method_metric(payload, "monte_carlo", "var_daily", "var")
    cvar_mc = _method_metric(payload, "monte_carlo", "cvar_daily", "cvar")

    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta_kpi(f"VaR histórico {confidence_label}", _format_pct(var_hist), subtexto="Pérdida umbral diaria observada.")
    with c2:
        tarjeta_kpi(f"VaR paramétrico {confidence_label}", _format_pct(var_param), subtexto="Estimación bajo supuestos paramétricos.")
    with c3:
        tarjeta_kpi(f"VaR Monte Carlo {confidence_label}", _format_pct(var_mc), subtexto="Estimación con simulaciones aleatorias.")

    c4, c5, c6 = st.columns(3)
    with c4:
        tarjeta_kpi(f"CVaR histórico {confidence_label}", _format_pct(cvar_hist), subtexto="Pérdida media condicional observada.")
    with c5:
        tarjeta_kpi(f"CVaR paramétrico {confidence_label}", _format_pct(cvar_param), subtexto="Cola esperada bajo distribución paramétrica.")
    with c6:
        tarjeta_kpi(f"CVaR Monte Carlo {confidence_label}", _format_pct(cvar_mc), subtexto="Cola esperada bajo simulación.")

    render_info_card(
        "Lectura técnica",
        (
            f"Con {confidence_label} de confianza, el VaR histórico diario es {_format_pct(var_hist)} y el CVaR histórico diario asciende a {_format_pct(cvar_hist)}. "
            f"El VaR paramétrico se estima en {_format_pct(var_param)} y el VaR Monte Carlo en {_format_pct(var_mc)}."
        ),
    )

with tab2:
    plot_card_header(
        "Distribución de rendimientos del portafolio",
        "Puedes activar o desactivar líneas de riesgo para simplificar la lectura.",
        modo=modo,
        caption="La leyenda lateral izquierda resume cada umbral de riesgo con colores distintos para evitar superposición visual.",
    )

    t1, t2, t3, t4 = st.columns(4)
    with t1:
        show_hist = st.checkbox("Histograma", value=True, key="var_show_hist")
    with t2:
        show_var = st.checkbox("Líneas VaR", value=True, key="var_show_var")
    with t3:
        show_cvar = st.checkbox("Líneas CVaR", value=True, key="var_show_cvar")
    with t4:
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
    st.plotly_chart(fig_dist, use_container_width=True)
    plot_card_footer(
        "La distribución permite ubicar visualmente dónde caen los umbrales VaR y CVaR frente a los rendimientos del portafolio."
    )

with tab3:
    seccion("Comparación VaR / CVaR")
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)

    seccion("Interpretación")
    render_info_card(
        "Lectura metodológica",
        "VaR paramétrico es útil cuando se asume una estructura más regular; VaR histórico se apoya en la distribución observada; Monte Carlo añade flexibilidad mediante simulación; y CVaR complementa al VaR porque mide la severidad media de la cola extrema.",
    )

    seccion("Backtesting VaR - Test de Kupiec")

    k1, k2, k3 = st.columns(3)
    with k1:
        tarjeta_kpi("Violaciones", str(_method_metric({'tmp': kupiec}, 'tmp', 'violations') or "N/D"), subtexto="Excesos observados frente al umbral estimado.")
    with k2:
        tarjeta_kpi("Observadas (%)", _format_pct(_method_metric({'tmp': kupiec}, 'tmp', 'observed_rate')), subtexto="Tasa real registrada en la muestra.")
    with k3:
        tarjeta_kpi("Esperadas (%)", _format_pct(_method_metric({'tmp': kupiec}, 'tmp', 'expected_rate')), subtexto="Tasa teórica coherente con el nivel de confianza.")

    render_info_card(
        "Conclusión de Kupiec",
        str(_method_metric({'tmp': kupiec}, 'tmp', 'conclusion') or "El backend no devolvió una conclusión textual de backtesting para este cálculo."),
    )