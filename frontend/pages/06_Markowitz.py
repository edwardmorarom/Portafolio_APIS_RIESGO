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


def _pick_value(payload: dict | None, *keys):
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _normalize_weights(raw_weights: list[float]) -> list[float]:
    total = sum(raw_weights)
    if total <= 0:
        return [1 / len(raw_weights)] * len(raw_weights)
    return [w / total for w in raw_weights]


def _build_frontier_payload(
    start: str,
    end: str,
    weights: list[float],
    risk_free_rate: float,
    n_portfolios: int,
    target_return: float | None,
    base_currency: str,
) -> dict:
    return {
        "tickers": [a["ticker"] for a in BASE_PORTFOLIO],
        "weights": weights,
        "start": start,
        "end": end,
        "risk_free_rate": risk_free_rate,
        "n_portfolios": n_portfolios,
        "target_return": target_return,
        "base_currency": base_currency,
    }


def _fetch_frontier(payload: dict) -> tuple[dict, str | None]:
    client = get_api_client()
    try:
        response = client.post_efficient_frontier(payload)
        if response is None:
            return {}, "El endpoint de frontera eficiente respondió vacío."
        if not isinstance(response, dict):
            return {}, f"Respuesta de Markowitz no válida: {type(response).__name__}"
        return response, None
    except ApiClientError as exc:
        return {}, exc.message
    except Exception as exc:
        return {}, f"Error inesperado consultando frontera eficiente: {exc}"


def _extract_frontier_df(payload: dict) -> pd.DataFrame:
    for key in [
        "frontier_points",
        "efficient_frontier",
        "simulated_portfolios",
        "portfolios",
        "points",
        "data",
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

            vol_col = pick("volatility", "risk", "std", "sigma")
            ret_col = pick("return", "expected_return", "retorno")
            sharpe_col = pick("sharpe", "sharpe_ratio")
            if vol_col and ret_col:
                out = pd.DataFrame(
                    {
                        "volatility": pd.to_numeric(df[vol_col], errors="coerce"),
                        "return": pd.to_numeric(df[ret_col], errors="coerce"),
                    }
                )
                if sharpe_col:
                    out["sharpe"] = pd.to_numeric(df[sharpe_col], errors="coerce")
                out = out.dropna(subset=["volatility", "return"])
                if not out.empty:
                    return out

    return pd.DataFrame(columns=["volatility", "return", "sharpe"])


def _extract_weights_df(obj: dict | None) -> pd.DataFrame:
    if not isinstance(obj, dict):
        return pd.DataFrame(columns=["Activo", "Peso", "Participación"])

    weights = obj.get("weights")
    if isinstance(weights, dict) and weights:
        rows = []
        for ticker, weight in weights.items():
            rows.append(
                {
                    "Activo": ticker,
                    "Peso": float(weight),
                    "Participación": f"{float(weight):.2%}",
                }
            )
        return (
            pd.DataFrame(rows)
            .sort_values("Peso", ascending=False)
            .reset_index(drop=True)
        )

    if isinstance(weights, list) and weights:
        rows = []
        tickers = obj.get("tickers") or [a["ticker"] for a in BASE_PORTFOLIO]
        for i, weight in enumerate(weights):
            ticker = tickers[i] if i < len(tickers) else f"Activo {i+1}"
            rows.append(
                {
                    "Activo": ticker,
                    "Peso": float(weight),
                    "Participación": f"{float(weight):.2%}",
                }
            )
        return (
            pd.DataFrame(rows)
            .sort_values("Peso", ascending=False)
            .reset_index(drop=True)
        )

    return pd.DataFrame(columns=["Activo", "Peso", "Participación"])


def _extract_named_block(payload: dict, *keys) -> dict:
    for key in keys:
        val = payload.get(key)
        if isinstance(val, dict):
            return val
    return {}


def _extract_min_var(payload: dict) -> dict:
    return _extract_named_block(payload, "minimum_variance", "min_variance_portfolio", "portfolio_min_variance")


def _extract_max_sharpe(payload: dict) -> dict:
    return _extract_named_block(payload, "maximum_sharpe", "max_sharpe_portfolio", "portfolio_max_sharpe")


def _extract_target(payload: dict) -> dict:
    return _extract_named_block(payload, "target_return_portfolio", "target_portfolio", "objective_portfolio")


def _extract_corr_df(payload: dict) -> pd.DataFrame:
    for key in ["correlation_matrix", "correlation", "corr_matrix"]:
        val = payload.get(key)
        if isinstance(val, dict) and val:
            df = pd.DataFrame(val)
            if not df.empty:
                return df
        if isinstance(val, list) and val:
            df = pd.DataFrame(val)
            if not df.empty:
                return df
    return pd.DataFrame()


def _metric_from_block(block: dict, *keys):
    if not isinstance(block, dict):
        return None
    return _pick_value(block, *keys)


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


def _build_corr_heatmap(corr_df: pd.DataFrame, modo: str, clean_view: bool) -> go.Figure:
    fig = go.Figure()

    if not corr_df.empty:
        fig.add_trace(
            go.Heatmap(
                z=corr_df.values,
                x=list(corr_df.columns),
                y=list(corr_df.index),
                zmin=-1,
                zmax=1,
                text=[[f"{v:.2f}" for v in row] for row in corr_df.values],
                texttemplate="%{text}",
                textfont={"size": 10},
                colorbar={"title": "Correlación"},
            )
        )

    return style_plotly_figure(
        fig,
        modo=modo,
        title="Matriz de correlación",
        xaxis_title="",
        yaxis_title="",
        show_xgrid=not clean_view,
        show_ygrid=not clean_view,
    )


def _build_frontier_figure(
    frontier_df: pd.DataFrame,
    min_var: dict,
    max_sharpe: dict,
    modo: str,
    show_cloud: bool,
    show_frontier: bool,
    show_optimal: bool,
    clean_view: bool,
) -> go.Figure:
    fig = go.Figure()

    if not frontier_df.empty:
        if show_cloud:
            marker_kwargs = {"size": 6, "opacity": 0.6}
            if "sharpe" in frontier_df.columns and frontier_df["sharpe"].notna().any():
                marker_kwargs["color"] = frontier_df["sharpe"]
                marker_kwargs["colorbar"] = {"title": "Sharpe"}
            fig.add_trace(
                go.Scatter(
                    x=frontier_df["volatility"],
                    y=frontier_df["return"],
                    mode="markers",
                    name="Portafolios",
                    marker=marker_kwargs,
                )
            )

        if show_frontier:
            frontier_line = frontier_df.sort_values("volatility")
            frontier_line = frontier_line.drop_duplicates(subset=["volatility"])
            frontier_line["cummax_return"] = frontier_line["return"].cummax()
            efficient = frontier_line[frontier_line["return"] >= frontier_line["cummax_return"] - 1e-12]

            fig.add_trace(
                go.Scatter(
                    x=efficient["volatility"],
                    y=efficient["return"],
                    mode="lines",
                    name="Frontera eficiente",
                    line=dict(width=2.8),
                )
            )

    if show_optimal:
        mv_ret = _metric_from_block(min_var, "expected_return", "return", "retorno")
        mv_vol = _metric_from_block(min_var, "volatility", "risk", "std")
        ms_ret = _metric_from_block(max_sharpe, "expected_return", "return", "retorno")
        ms_vol = _metric_from_block(max_sharpe, "volatility", "risk", "std")

        if mv_ret is not None and mv_vol is not None:
            fig.add_trace(
                go.Scatter(
                    x=[mv_vol],
                    y=[mv_ret],
                    mode="markers",
                    name="Mínima varianza",
                    marker=dict(size=11, symbol="diamond"),
                )
            )

        if ms_ret is not None and ms_vol is not None:
            fig.add_trace(
                go.Scatter(
                    x=[ms_vol],
                    y=[ms_ret],
                    mode="markers",
                    name="Máximo Sharpe",
                    marker=dict(size=12, symbol="star"),
                )
            )

    return style_plotly_figure(
        fig,
        modo=modo,
        title="Frontera eficiente",
        xaxis_title="Volatilidad",
        yaxis_title="Retorno",
        show_xgrid=not clean_view,
        show_ygrid=not clean_view,
    )


def _module_reading(
    min_var: dict,
    max_sharpe: dict,
    n_assets: int,
    observations,
    n_portfolios: int,
    risk_free_rate: float,
) -> str:
    mv_ret = _metric_from_block(min_var, "expected_return", "return", "retorno")
    mv_vol = _metric_from_block(min_var, "volatility", "risk", "std")
    ms_ret = _metric_from_block(max_sharpe, "expected_return", "return", "retorno")
    ms_sharpe = _metric_from_block(max_sharpe, "sharpe", "sharpe_ratio")

    return (
        f"Se analizaron {n_assets} activos con {observations} observaciones alineadas y se simularon {n_portfolios:,} "
        f"portafolios usando una tasa libre de riesgo de {_format_pct(risk_free_rate)}."
        f" El portafolio de mínima varianza ofrece un retorno esperado de {_format_pct(mv_ret)} con volatilidad de {_format_pct(mv_vol)}, "
        f"mientras que el portafolio de máximo Sharpe alcanza un retorno esperado de {_format_pct(ms_ret)} con Sharpe de {_format_num(ms_sharpe, 3)}."
    )


help_map, _ = _fetch_help()

modo, filtros_sidebar = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    modo_default="General",
    filtros_label="Parámetros de Optimización",
    filtros_expanded=False,
)

today = pd.Timestamp.today().normalize()

with filtros_sidebar:
    horizonte = st.selectbox(
        "Horizonte de análisis",
        ["1 mes", "Trimestre", "Semestre", "1 año", "3 años", "5 años", "Personalizado"],
        index=3,
        key="markowitz_horizonte_backend",
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
                key="markowitz_custom_start",
            )
        with c2:
            custom_end = st.date_input(
                "Fecha final",
                value=today.date(),
                max_value=today.date(),
                key="markowitz_custom_end",
            )

    risk_free_rate = st.number_input(
        "Tasa libre de riesgo (%)",
        min_value=0.0,
        max_value=20.0,
        value=3.0,
        step=0.1,
        key="markowitz_rf",
    ) / 100.0

    n_portfolios = st.slider(
        "Número de portafolios",
        min_value=5000,
        max_value=50000,
        value=10000,
        step=1000,
        key="markowitz_n_portfolios",
    )

    target_return_pct = st.number_input(
        "Retorno anual objetivo del portafolio (%)",
        min_value=0.0,
        max_value=50.0,
        value=10.0,
        step=0.5,
        key="markowitz_target_return",
    ) / 100.0

    base_currency = st.selectbox(
        "Moneda base",
        ["USD", "EUR", "COP"],
        index=0,
        key="markowitz_base_currency",
    )

start_date, end_date = _resolve_dates(
    horizonte=horizonte,
    default_end=today,
    custom_start=pd.Timestamp(custom_start) if custom_start is not None else None,
    custom_end=pd.Timestamp(custom_end) if custom_end is not None else None,
)

if start_date >= end_date:
    st.error("La fecha inicial debe ser menor que la fecha final.")
    st.stop()

request_payload = _build_frontier_payload(
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
    weights=_normalize_weights([1.0] * len(BASE_PORTFOLIO)),
    risk_free_rate=risk_free_rate,
    n_portfolios=n_portfolios,
    target_return=target_return_pct,
    base_currency=base_currency,
)

payload, frontier_error = _fetch_frontier(request_payload)

header_dashboard(
    "Módulo 6 - Markowitz",
    "Construye y compara carteras sobre la frontera eficiente para estudiar riesgo, retorno y eficiencia",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo construye múltiples combinaciones de portafolios para identificar aquellas que ofrecen una mejor relación entre retorno esperado y riesgo. Se resaltan el portafolio de mínima varianza, el de máximo Sharpe y una solución con retorno objetivo."
    )
else:
    nota(
        "En modo estadístico se enfatizan la matriz de correlación, la frontera eficiente, la composición de portafolios óptimos y los indicadores de eficiencia."
    )

if frontier_error:
    st.error(frontier_error)
    st.stop()

if not isinstance(payload, dict) or not payload:
    st.error("No se recibieron datos válidos del endpoint de optimización.")
    st.stop()

frontier_df = _extract_frontier_df(payload)
corr_df = _extract_corr_df(payload)
min_var = _extract_min_var(payload)
max_sharpe = _extract_max_sharpe(payload)
target_port = _extract_target(payload)

min_var_df = _extract_weights_df(min_var)
max_sharpe_df = _extract_weights_df(max_sharpe)
target_df = _extract_weights_df(target_port)

observations = _pick_value(payload, "observations", "n_observations", "sample_size")
n_assets = _pick_value(payload, "n_assets", "num_assets") or len(BASE_PORTFOLIO)

tab1, tab2, tab3 = st.tabs(
    ["Portafolios destacados", "Gráficas", "Composición óptima"]
)

with tab1:
    seccion("Portafolios destacados")

    mv_ret = _metric_from_block(min_var, "expected_return", "return", "retorno")
    mv_vol = _metric_from_block(min_var, "volatility", "risk", "std")
    ms_ret = _metric_from_block(max_sharpe, "expected_return", "return", "retorno")
    ms_sharpe = _metric_from_block(max_sharpe, "sharpe", "sharpe_ratio")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tarjeta_kpi(
            "Retorno mín. varianza",
            _format_pct(mv_ret),
            subtexto="Rentabilidad asociada a la cartera de menor volatilidad.",
            help_text="Retorno esperado del portafolio de mínima varianza.",
        )

    with c2:
        tarjeta_kpi(
            "Volatilidad mín. varianza",
            _format_pct(mv_vol),
            subtexto="Menor riesgo disponible.",
            help_text="Nivel mínimo de riesgo dentro del conjunto simulado.",
        )

    with c3:
        tarjeta_kpi(
            "Retorno máx. Sharpe",
            _format_pct(ms_ret),
            subtexto="Rentabilidad esperada del mejor balance riesgo-retorno.",
            help_text="Retorno esperado del portafolio con máximo Sharpe.",
        )

    with c4:
        tarjeta_kpi(
            "Sharpe máximo",
            _format_num(ms_sharpe, 3),
            subtexto="Mejor eficiencia riesgo-retorno.",
            help_text="Exceso de retorno por unidad de volatilidad.",
        )

    plot_card_footer(
        _module_reading(
            min_var=min_var,
            max_sharpe=max_sharpe,
            n_assets=int(n_assets),
            observations=observations,
            n_portfolios=n_portfolios,
            risk_free_rate=risk_free_rate,
        )
    )

    seccion("KPIs del módulo")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        tarjeta_kpi(
            "Activos analizados",
            str(int(n_assets)),
            subtexto="Universo usado para construir combinaciones factibles.",
            help_text="Número de activos enviados al optimizador.",
        )
    with k2:
        tarjeta_kpi(
            "Observaciones",
            str(observations) if observations is not None else "N/D",
            subtexto="Muestra histórica disponible para covarianzas y retornos.",
            help_text="Cantidad de observaciones útiles para estimación.",
        )
    with k3:
        tarjeta_kpi(
            "Portafolios simulados",
            f"{n_portfolios:,}".replace(",", "."),
            subtexto="Exploración aleatoria del espacio riesgo-retorno.",
            help_text="Número de combinaciones generadas.",
        )
    with k4:
        tarjeta_kpi(
            "Tasa libre de riesgo",
            _format_pct(risk_free_rate),
            subtexto="Referencia para medir eficiencia ajustada por riesgo.",
            help_text="Usada en el cálculo de Sharpe.",
        )

    plot_card_footer(
        f"Se analizaron {int(n_assets)} activos con {observations} observaciones alineadas y se simularon {n_portfolios:,} portafolios usando una tasa libre de riesgo de {_format_pct(risk_free_rate)}.".replace(",", ".")
    )

    seccion("Interpretación")
    render_info_card(
        "Lectura del módulo",
        "Este módulo muestra que no existe una única mejor cartera: todo depende del equilibrio entre retorno y riesgo. La frontera eficiente resume las combinaciones más convenientes, mientras que mínima varianza, máximo Sharpe y retorno objetivo representan decisiones distintas dentro del mismo problema.",
    )

with tab2:
    seccion("Visualizaciones de optimización")

    g1, g2 = st.columns(2, gap="large")

    with g1:
        plot_card_header(
            "Matriz de correlación",
            "Muestra qué tan relacionados están los activos entre sí y ayuda a juzgar el potencial de diversificación.",
            modo=modo,
            caption="Activa o desactiva detalles para simplificar la lectura visual de la matriz.",
        )

        o1, o2 = st.columns(2)
        with o1:
            corr_clean = st.checkbox("Vista limpia", value=False, key="markowitz_corr_clean")
        with o2:
            show_corr_table = st.checkbox("Ver tabla de correlación", value=False, key="markowitz_corr_table")

        fig_corr = _build_corr_heatmap(corr_df, modo=modo, clean_view=corr_clean)
        st.plotly_chart(fig_corr, width="stretch")
        plot_card_footer(
            "La matriz de correlación ayuda a identificar qué tan parecidos son los movimientos entre activos. Correlaciones más bajas suelen mejorar el potencial de diversificación del portafolio."
        )

        if show_corr_table and not corr_df.empty:
            st.dataframe(corr_df, width="stretch")

    with g2:
        plot_card_header(
            "Frontera eficiente",
            "Resume el universo de portafolios simulados y resalta los puntos óptimos más relevantes.",
            modo=modo,
            caption="Mejoré leyenda, ejes y contraste para una lectura más clara.",
        )

        p1, p2, p3, p4 = st.columns(4)
        with p1:
            show_cloud = st.checkbox("Nube", value=True, key="markowitz_show_cloud")
        with p2:
            show_frontier = st.checkbox("Frontera", value=True, key="markowitz_show_frontier")
        with p3:
            show_optimal = st.checkbox("Óptimos", value=True, key="markowitz_show_optimal")
        with p4:
            frontier_clean = st.checkbox("Vista limpia", value=False, key="markowitz_frontier_clean")

        fig_frontier = _build_frontier_figure(
            frontier_df=frontier_df,
            min_var=min_var,
            max_sharpe=max_sharpe,
            modo=modo,
            show_cloud=show_cloud,
            show_frontier=show_frontier,
            show_optimal=show_optimal,
            clean_view=frontier_clean,
        )
        st.plotly_chart(fig_frontier, width="stretch")
        plot_card_footer(
            "La frontera eficiente resume las mejores combinaciones riesgo-retorno encontradas. Los portafolios destacados permiten comparar estabilidad, eficiencia y metas de rentabilidad."
        )

    seccion("KPIs del módulo")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        tarjeta_kpi("Activos analizados", str(int(n_assets)), subtexto="Universo usado para construir combinaciones factibles.")
    with k2:
        tarjeta_kpi("Observaciones", str(observations) if observations is not None else "N/D", subtexto="Muestra histórica disponible para covarianzas y retornos.")
    with k3:
        tarjeta_kpi("Portafolios simulados", f"{n_portfolios:,}".replace(",", "."), subtexto="Exploración aleatoria del espacio riesgo-retorno.")
    with k4:
        tarjeta_kpi("Tasa libre de riesgo", _format_pct(risk_free_rate), subtexto="Referencia para medir eficiencia ajustada por riesgo.")

    plot_card_footer(
        f"Se analizaron {int(n_assets)} activos con {observations} observaciones alineadas y se simularon {n_portfolios:,} portafolios usando una tasa libre de riesgo de {_format_pct(risk_free_rate)}.".replace(",", ".")
    )

    seccion("Interpretación")
    render_info_card(
        "Lectura gráfica",
        "La dispersión de portafolios permite ver el trade-off entre riesgo y retorno. La curva eficiente concentra las soluciones dominantes, mientras que la matriz de correlación ayuda a explicar por qué ciertas combinaciones ofrecen más diversificación que otras.",
    )

with tab3:
    seccion("Composición de portafolios óptimos")

    c1, c2 = st.columns(2, gap="large")

    with c1:
        plot_card_header(
            "Portafolio de mínima varianza",
            "Composición del portafolio con menor riesgo dentro del conjunto estimado.",
            modo=modo,
            caption="Ordenado de mayor a menor participación.",
        )
        st.dataframe(min_var_df, width="stretch", hide_index=True)

    with c2:
        plot_card_header(
            "Portafolio de máximo Sharpe",
            "Composición del portafolio con mejor relación retorno-riesgo.",
            modo=modo,
            caption="Ordenado de mayor a menor participación.",
        )
        st.dataframe(max_sharpe_df, width="stretch", hide_index=True)

    seccion("Optimización con retorno objetivo")

    target_ret = _metric_from_block(target_port, "expected_return", "return", "retorno")
    target_vol = _metric_from_block(target_port, "volatility", "risk", "std")

    t1, t2 = st.columns([1.05, 1.2], gap="large")
    with t1:
        plot_card_header(
            "Solución condicionada",
            "Cartera asociada al retorno objetivo configurado en el panel lateral.",
            modo=modo,
            caption=f"Retorno objetivo configurado actualmente: {_format_pct(target_return_pct)}",
        )
        tarjeta_kpi(
            "Retorno esperado",
            _format_pct(target_ret),
            subtexto="Objetivo alcanzado.",
            help_text="Rentabilidad estimada de la solución condicionada.",
        )
        tarjeta_kpi(
            "Volatilidad",
            _format_pct(target_vol),
            subtexto="Riesgo asociado al retorno objetivo impuesto.",
            help_text="Riesgo esperado de la cartera objetivo.",
        )

    with t2:
        st.dataframe(target_df, width="stretch", hide_index=True)

    seccion("KPIs del módulo")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        tarjeta_kpi("Activos analizados", str(int(n_assets)), subtexto="Universo usado para construir combinaciones factibles.")
    with k2:
        tarjeta_kpi("Observaciones", str(observations) if observations is not None else "N/D", subtexto="Muestra histórica disponible para covarianzas y retornos.")
    with k3:
        tarjeta_kpi("Portafolios simulados", f"{n_portfolios:,}".replace(",", "."), subtexto="Exploración aleatoria del espacio riesgo-retorno.")
    with k4:
        tarjeta_kpi("Tasa libre de riesgo", _format_pct(risk_free_rate), subtexto="Referencia para medir eficiencia ajustada por riesgo.")

    plot_card_footer(
        f"Se analizaron {int(n_assets)} activos con {observations} observaciones alineadas y se simularon {n_portfolios:,} portafolios usando una tasa libre de riesgo de {_format_pct(risk_free_rate)}.".replace(",", ".")
    )

    seccion("Interpretación")
    render_info_card(
        "Lectura composicional",
        "La composición óptima muestra cómo cambia el peso relativo de cada activo según el criterio elegido. Mínima varianza privilegia estabilidad, máximo Sharpe eficiencia, y retorno objetivo una meta explícita de rentabilidad.",
    )