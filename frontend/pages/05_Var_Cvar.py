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


def _format_money(x) -> str:
    if x is None:
        return "N/D"
    try:
        return f"USD {float(x):,.2f}"
    except Exception:
        return str(x)


def _money_risk(portfolio_value: float, risk_pct) -> float | None:
    if risk_pct is None:
        return None
    try:
        return float(portfolio_value) * float(risk_pct)
    except Exception:
        return None


def _fetch_var(
    tickers: list[str],
    weights: list[float],
    start: str,
    end: str,
    alpha: float,
    n_sim: int,
    distribution: str,
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
        "distribution": distribution,
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


def _comparison_table(payload: dict, portfolio_value: float) -> pd.DataFrame:
    rows = []

    for key, label in [
        ("historical", "Histórico"),
        ("parametric", "Paramétrico"),
        ("monte_carlo", "Monte Carlo"),
    ]:
        method = payload.get(key, {})
        if not isinstance(method, dict):
            continue

        var_daily = method.get("var_daily")
        cvar_daily = method.get("cvar_daily")
        var_annualized = method.get("var_annualized")
        cvar_annualized = method.get("cvar_annualized")

        rows.append(
            {
                "Método": label,
                "Distribución": str(method.get("distribution", "N/D")),
                "VaR diario": _format_pct(var_daily),
                "CVaR diario": _format_pct(cvar_daily),
                "VaR monetario diario": _format_money(_money_risk(portfolio_value, var_daily)),
                "CVaR monetario diario": _format_money(_money_risk(portfolio_value, cvar_daily)),
                "VaR anualizado": _format_pct(var_annualized),
                "CVaR anualizado": _format_pct(cvar_annualized),
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
                opacity=0.72,
                nbinsx=35,
                marker=dict(
                    color="rgba(59, 130, 246, 0.42)",
                    line=dict(color="rgba(29, 78, 216, 0.45)", width=0.6),
                ),
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
                loss_value = float(value)
                x_value = -loss_value

                fig.add_vline(
                    x=x_value,
                    line_dash="dash",
                    line_width=3.0,
                    line_color=color,
                    opacity=0.95,
                )

                line_specs.append(
                    {
                        "section": "VaR",
                        "label": label,
                        "color": color,
                        "loss_value": loss_value,
                        "x_value": x_value,
                        "dash": "dash",
                    }
                )

    if show_cvar:
        for method_name, label, color in [
            ("parametric", "CVaR Paramétrico", "#DC2626"),
            ("historical", "CVaR Histórico", "#D97706"),
            ("monte_carlo", "CVaR Monte Carlo", "#BE185D"),
        ]:
            value = _method_metric(payload, method_name, "cvar_daily", "cvar")
            if value is not None:
                loss_value = float(value)
                x_value = -loss_value

                fig.add_vline(
                    x=x_value,
                    line_dash="dot",
                    line_width=3.0,
                    line_color=color,
                    opacity=0.95,
                )

                line_specs.append(
                    {
                        "section": "CVaR",
                        "label": label,
                        "color": color,
                        "loss_value": loss_value,
                        "x_value": x_value,
                        "dash": "dot",
                    }
                )

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
        plot_bgcolor="#EEF4FF" if modo == "General" else "#F8EAF1",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=24, r=24, t=84, b=24),
    )

    if line_specs:
        # Panel de leyenda más grande, limpio y con líneas reales dash/dot
        panel_x0 = 0.012
        panel_x1 = 0.36
        panel_y1 = 0.985

        rows = []
        var_items = [item for item in line_specs if item["section"] == "VaR"]
        cvar_items = [item for item in line_specs if item["section"] == "CVaR"]

        if var_items:
            rows.append({"type": "header", "text": "VaR"})
            rows.extend(var_items)

        if cvar_items:
            rows.append({"type": "space"})
            rows.append({"type": "header", "text": "CVaR"})
            rows.extend(cvar_items)

        row_gap = 0.052
        panel_height = max(0.18, len(rows) * row_gap + 0.035)
        panel_y0 = max(0.03, panel_y1 - panel_height)

        fig.add_shape(
            type="rect",
            xref="paper",
            yref="paper",
            x0=panel_x0,
            x1=panel_x1,
            y0=panel_y0,
            y1=panel_y1,
            line=dict(color="rgba(15,23,42,0.18)", width=1),
            fillcolor="rgba(255,255,255,0.92)",
            layer="above",
        )

        current_y = panel_y1 - 0.025

        for row in rows:
            if row.get("type") == "space":
                current_y -= row_gap * 0.45
                continue

            if row.get("type") == "header":
                fig.add_annotation(
                    xref="paper",
                    yref="paper",
                    x=panel_x0 + 0.018,
                    y=current_y,
                    xanchor="left",
                    yanchor="middle",
                    showarrow=False,
                    text=f"<b>{row['text']}</b>",
                    font=dict(size=12, color="#0F172A"),
                )
                current_y -= row_gap
                continue

            dash_style = row["dash"]
            color = row["color"]
            label = row["label"]
            loss_value = row["loss_value"]

            # Línea de muestra en la leyenda, con el mismo dash/dot que la línea del gráfico
            fig.add_shape(
                type="line",
                xref="paper",
                yref="paper",
                x0=panel_x0 + 0.020,
                x1=panel_x0 + 0.070,
                y0=current_y,
                y1=current_y,
                line=dict(
                    color=color,
                    width=3,
                    dash=dash_style,
                ),
                layer="above",
            )

            fig.add_annotation(
                xref="paper",
                yref="paper",
                x=panel_x0 + 0.080,
                y=current_y,
                xanchor="left",
                yanchor="middle",
                showarrow=False,
                text=f"{label}: pérdida {_format_pct(loss_value)}",
                font=dict(size=10.8, color="#0F172A"),
            )

            current_y -= row_gap

        # Nota corta para aclarar por qué las líneas quedan en negativo
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=panel_x0 + 0.018,
            y=panel_y0 + 0.018,
            xanchor="left",
            yanchor="bottom",
            showarrow=False,
            text="<span style='font-size:10px;color:#475569;'>Líneas ubicadas en la cola izquierda: -VaR y -CVaR</span>",
        )

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

    alpha_pct = st.number_input(
        "Nivel de confianza (%)",
        min_value=95.0,
        max_value=99.99,
        value=95.0,
        step=0.01,
        key="var_alpha_manual",
        format="%.2f",
        help="Nivel de confianza del VaR. Debe estar entre 95% y 99.99%.",
    )

    alpha = alpha_pct / 100.0
    alpha_label = f"{alpha_pct:.2f}%"

    distribution_label = st.selectbox(
        "Distribución",
        ["Normal", "t-Student"],
        index=0,
        key="var_distribution",
        help=(
            "La normal es el supuesto clásico del VaR paramétrico. "
            "La t-Student permite colas más pesadas y suele ser más realista para rendimientos financieros."
        ),
    )
    distribution = "t" if distribution_label == "t-Student" else "normal"

    base_currency = st.selectbox(
        "Moneda base",
        ["USD"],
        index=0,
        key="var_base_currency",
        help="El portafolio se trabaja en USD después de convertir históricamente los precios desde su moneda local.",
    )

    portfolio_value = st.number_input(
        "Valor portafolio",
        min_value=1000.0,
        max_value=100000000.0,
        value=100000.0,
        step=1000.0,
        key="var_portfolio_value",
        format="%.2f",
        help="Monto invertido. Se usa para convertir VaR y CVaR porcentual a pérdida monetaria estimada.",
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
        distribution=distribution,
        return_type="log",
    )

header_dashboard(
    "Mód. 5: VaR y CVaR",
    "Cuantifica la pérdida potencial porcentual y monetaria del portafolio.",
    modo=modo,
)

if modo == "General":
    nota(
        "Incluye VaR paramétrico, VaR histórico, VaR Monte Carlo, Expected Shortfall, VaR monetario, CVaR monetario, distribución Normal/t-Student y backtesting de Kupiec."
    )
else:
    nota(
        "En modo estadístico se enfatiza la comparación de métodos, la distribución de rendimientos, el backtesting del VaR y la conversión monetaria del riesgo."
    )

if abs(total_pct - 100.0) > 1e-6:
    st.error("Los pesos del portafolio deben sumar exactamente 100% para calcular VaR/CVaR.")
    st.stop()

if risk_error:
    st.error(risk_error)
    st.stop()

returns_s = _extract_distribution_series(payload)
kupiec = _extract_kupiec(payload)
comparison_df = _comparison_table(payload, portfolio_value=portfolio_value)

render_meta_row(
    [
        ("Confianza", alpha_label),
        ("Moneda", base_currency),
        ("Portafolio", _format_money(portfolio_value)),
        ("Distribución", distribution_label),
        ("Simulaciones", f"{mc_n_sims:,}".replace(",", ".")),
        ("Horizonte", horizonte),
    ]
)

tab1, tab2, tab3 = st.tabs(["Resumen y KPIs", "Distribución de riesgo", "Comparación y backtesting"])

with tab1:
    seccion("Resumen VaR / CVaR")

    confidence_label = alpha_label

    var_hist = _method_metric(payload, "historical", "var_daily", "var")
    cvar_hist = _method_metric(payload, "historical", "cvar_daily", "cvar")
    var_param = _method_metric(payload, "parametric", "var_daily", "var")
    cvar_param = _method_metric(payload, "parametric", "cvar_daily", "cvar")
    var_mc = _method_metric(payload, "monte_carlo", "var_daily", "var")
    cvar_mc = _method_metric(payload, "monte_carlo", "cvar_daily", "cvar")

    var_hist_money = _money_risk(portfolio_value, var_hist)
    cvar_hist_money = _money_risk(portfolio_value, cvar_hist)
    var_param_money = _money_risk(portfolio_value, var_param)
    cvar_param_money = _money_risk(portfolio_value, cvar_param)
    var_mc_money = _money_risk(portfolio_value, var_mc)
    cvar_mc_money = _money_risk(portfolio_value, cvar_mc)

    c1, c2, c3 = st.columns(3)

    with c1:
        tarjeta_kpi(
            f"VaR histórico {confidence_label}",
            _format_pct(var_hist),
            subtexto="Pérdida umbral diaria observada.",
            help_text="VaR histórico usa la distribución empírica de retornos del portafolio.",
        )

    with c2:
        tarjeta_kpi(
            f"VaR paramétrico {confidence_label}",
            _format_pct(var_param),
            subtexto="Estimación bajo supuestos paramétricos.",
            help_text=(
                "VaR paramétrico aproxima la pérdida usando media, volatilidad y una distribución teórica. "
                "Con t-Student se asigna mayor peso a eventos extremos que con la normal."
            ),
        )

    with c3:
        tarjeta_kpi(
            f"VaR Monte Carlo {confidence_label}",
            _format_pct(var_mc),
            subtexto="Estimación con simulaciones aleatorias.",
            help_text="VaR Monte Carlo simula escenarios de retornos para estimar la cola de pérdidas.",
        )

    c4, c5, c6 = st.columns(3)

    with c4:
        tarjeta_kpi(
            f"CVaR histórico {confidence_label}",
            _format_pct(cvar_hist),
            subtexto="Pérdida media condicional observada.",
            help_text="CVaR mide la pérdida promedio cuando se supera el umbral VaR.",
        )

    with c5:
        tarjeta_kpi(
            f"CVaR paramétrico {confidence_label}",
            _format_pct(cvar_param),
            subtexto="Cola esperada bajo distribución paramétrica.",
            help_text=(
                "Expected Shortfall paramétrico estima la pérdida esperada en la cola bajo supuestos teóricos. "
                "La t-Student suele producir colas más pesadas que la normal."
            ),
        )

    with c6:
        tarjeta_kpi(
            f"CVaR Monte Carlo {confidence_label}",
            _format_pct(cvar_mc),
            subtexto="Cola esperada bajo simulación.",
            help_text="CVaR Monte Carlo promedia las peores pérdidas simuladas.",
        )

    seccion("Riesgo monetario diario")

    m1, m2, m3 = st.columns(3)

    with m1:
        tarjeta_kpi(
            f"VaR histórico monetario {confidence_label}",
            _format_money(var_hist_money),
            subtexto="Pérdida diaria estimada en dinero.",
            help_text="VaR monetario = valor del portafolio multiplicado por VaR porcentual.",
        )

    with m2:
        tarjeta_kpi(
            f"VaR paramétrico monetario {confidence_label}",
            _format_money(var_param_money),
            subtexto="Pérdida diaria estimada en dinero.",
            help_text="Convierte el VaR paramétrico porcentual a pérdida monetaria.",
        )

    with m3:
        tarjeta_kpi(
            f"VaR Monte Carlo monetario {confidence_label}",
            _format_money(var_mc_money),
            subtexto="Pérdida diaria estimada en dinero.",
            help_text="Convierte el VaR Monte Carlo porcentual a pérdida monetaria.",
        )

    m4, m5, m6 = st.columns(3)

    with m4:
        tarjeta_kpi(
            f"CVaR histórico monetario {confidence_label}",
            _format_money(cvar_hist_money),
            subtexto="Pérdida media en escenarios extremos.",
            help_text="CVaR monetario = valor del portafolio multiplicado por CVaR porcentual.",
        )

    with m5:
        tarjeta_kpi(
            f"CVaR paramétrico monetario {confidence_label}",
            _format_money(cvar_param_money),
            subtexto="Pérdida media en escenarios extremos.",
            help_text="Convierte el CVaR paramétrico porcentual a pérdida monetaria.",
        )

    with m6:
        tarjeta_kpi(
            f"CVaR Monte Carlo monetario {confidence_label}",
            _format_money(cvar_mc_money),
            subtexto="Pérdida media en escenarios extremos.",
            help_text="Convierte el CVaR Monte Carlo porcentual a pérdida monetaria.",
        )

    render_info_card(
        "Lectura técnica",
        (
            f"Con un portafolio de {_format_money(portfolio_value)} y un nivel de confianza de {confidence_label}, "
            f"el VaR histórico diario es {_format_pct(var_hist)}, equivalente a una pérdida monetaria aproximada de {_format_money(var_hist_money)}. "
            f"El CVaR histórico diario es {_format_pct(cvar_hist)}, equivalente a una pérdida media esperada de {_format_money(cvar_hist_money)} "
            "en los escenarios que caen dentro de la cola extrema."
        ),
    )

with tab2:
    plot_card_header(
        "Distribución de rendimientos del portafolio",
        "La distribución permite ubicar los umbrales de pérdida VaR y CVaR en la cola izquierda de los retornos.",
        modo=modo,
        caption="Las líneas se grafican como pérdidas negativas para quedar ubicadas correctamente en la cola izquierda.",
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

    st.plotly_chart(fig_dist, width="stretch")

    plot_card_footer(
        "VaR y CVaR son pérdidas positivas como métrica, pero se dibujan con signo negativo para representar la cola izquierda de los retornos."
    )

with tab3:
    seccion("Comparación VaR / CVaR")

    st.dataframe(comparison_df, width="stretch", hide_index=True)

    seccion("Interpretación")

    render_info_card(
        "Lectura metodológica",
        (
            "VaR paramétrico es útil cuando se asume una distribución teórica. En este módulo puede calcularse con Normal o t-Student. "
            "La distribución t-Student permite colas más pesadas y suele ser más realista para rendimientos financieros extremos. "
            "VaR histórico se apoya en la distribución observada; Monte Carlo añade flexibilidad mediante simulación; "
            "y CVaR complementa al VaR porque mide la severidad media de la cola extrema. "
            "La versión monetaria ayuda a traducir porcentajes de riesgo a pérdidas aproximadas en dinero."
        ),
    )

    seccion("Backtesting VaR - Test de Kupiec")

    k1, k2, k3 = st.columns(3)

    with k1:
        tarjeta_kpi(
            "Violaciones",
            str(_method_metric({"tmp": kupiec}, "tmp", "violations") or "N/D"),
            subtexto="Excesos observados frente al umbral estimado.",
            help_text="Cuenta cuántas veces la pérdida observada superó el VaR estimado.",
        )

    with k2:
        tarjeta_kpi(
            "Observadas (%)",
            _format_pct(_method_metric({"tmp": kupiec}, "tmp", "observed_rate")),
            subtexto="Tasa real registrada en la muestra.",
            help_text="Proporción de violaciones observadas en la muestra histórica.",
        )

    with k3:
        tarjeta_kpi(
            "Esperadas (%)",
            _format_pct(_method_metric({"tmp": kupiec}, "tmp", "expected_rate")),
            subtexto="Tasa teórica coherente con el nivel de confianza.",
            help_text="Si la confianza es 95%, la tasa esperada de violaciones es cercana al 5%.",
        )

    render_info_card(
        "Conclusión de Kupiec",
        str(
            _method_metric({"tmp": kupiec}, "tmp", "conclusion")
            or "El backend no devolvió una conclusión textual de backtesting para este cálculo."
        ),
    )