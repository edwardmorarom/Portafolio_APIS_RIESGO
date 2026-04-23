from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card
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


def _weights_editor(sidebar_container, key_prefix: str) -> tuple[list[float], float]:
    with sidebar_container:
        st.markdown("**Pesos de referencia del portafolio (%)**")
        weights_pct: list[float] = []
        for asset in BASE_PORTFOLIO:
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
            st.warning("Estos pesos son de referencia visual. La optimización de Markowitz sigue calculándose sobre el universo seleccionado.")

    return [w / 100.0 for w in weights_pct], total_pct


def _build_frontier_payload(
    start: str,
    end: str,
    risk_free_rate: float,
    n_portfolios: int,
    target_return: float | None,
    risk_profile: str | None,
    reference_weights: list[float],
) -> dict:
    return {
        "tickers": [a["ticker"] for a in BASE_PORTFOLIO],
        "start": start,
        "end": end,
        "rf_annual": risk_free_rate,
        "n_portfolios": n_portfolios,
        "target_return_annual": target_return,
        "risk_profile": risk_profile,
        "return_type": "log",
        "weights": reference_weights,
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
    for key in ["frontier", "frontier_points", "efficient_frontier", "points"]:
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
                return out.dropna(subset=["volatility", "return"]).reset_index(drop=True)

    return pd.DataFrame(columns=["volatility", "return", "sharpe"])


def _extract_simulated_df(payload: dict) -> pd.DataFrame:
    for key in ["simulated_portfolios", "portfolios", "cloud", "nube"]:
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
                return out.dropna(subset=["volatility", "return"]).reset_index(drop=True)

    return pd.DataFrame(columns=["volatility", "return", "sharpe"])


def _extract_named_block(payload: dict, *keys) -> dict:
    for key in keys:
        val = payload.get(key)
        if isinstance(val, dict):
            return val
    return {}


def _extract_min_var(payload: dict) -> dict:
    return _extract_named_block(payload, "min_variance", "minimum_variance", "min_variance_portfolio")


def _extract_max_sharpe(payload: dict) -> dict:
    return _extract_named_block(payload, "max_sharpe", "maximum_sharpe", "max_sharpe_portfolio")


def _extract_target(payload: dict) -> dict:
    return _extract_named_block(payload, "target_return_portfolio", "target_portfolio")


def _extract_profile_suggestion(payload: dict) -> dict:
    return _extract_named_block(payload, "suggested_profile_portfolio", "profile_portfolio")


def _extract_weights_df(obj: dict | None) -> pd.DataFrame:
    if not isinstance(obj, dict):
        return pd.DataFrame(columns=["Activo", "Peso", "Participación"])

    weights = obj.get("weights")

    if isinstance(weights, list) and weights:
        rows = []
        for item in weights:
            if isinstance(item, dict) and "asset" in item and "weight" in item:
                rows.append(
                    {
                        "Activo": str(item["asset"]),
                        "Peso": float(item["weight"]),
                        "Participación": f"{float(item['weight']):.2%}",
                    }
                )
        if rows:
            return pd.DataFrame(rows).sort_values("Peso", ascending=False).reset_index(drop=True)

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
        return pd.DataFrame(rows).sort_values("Peso", ascending=False).reset_index(drop=True)

    return pd.DataFrame(columns=["Activo", "Peso", "Participación"])


def _extract_reference_weights_df(weights: list[float]) -> pd.DataFrame:
    rows = []
    for asset, weight in zip(BASE_PORTFOLIO, weights):
        rows.append(
            {
                "Activo": asset["ticker"],
                "Peso": float(weight),
                "Participación": f"{float(weight):.2%}",
            }
        )
    return pd.DataFrame(rows).sort_values("Peso", ascending=False).reset_index(drop=True)


def _extract_corr_df(payload: dict) -> pd.DataFrame:
    for key in ["correlation_matrix", "correlation", "corr_matrix"]:
        val = payload.get(key)
        if isinstance(val, dict) and val:
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
                colorscale=[
                    [0.0, "#1D4ED8"],
                    [0.5, "#F8FAFC"],
                    [1.0, "#8A1538"],
                ],
                colorbar={"title": "Correlación"},
            )
        )

    fig = style_plotly_figure(
        fig,
        modo=modo,
        title="",
        xaxis_title="",
        yaxis_title="",
        show_xgrid=not clean_view,
        show_ygrid=not clean_view,
    )
    fig.update_layout(
        margin=dict(l=24, r=24, t=24, b=24),
        showlegend=False,
        plot_bgcolor="#EEF4FF" if modo == "General" else "#FBEAF1",
    )
    return fig


def _build_frontier_figure(
    frontier_df: pd.DataFrame,
    simulated_df: pd.DataFrame,
    min_var: dict,
    max_sharpe: dict,
    modo: str,
    show_cloud: bool,
    show_frontier: bool,
    show_optimal: bool,
    clean_view: bool,
) -> go.Figure:
    fig = go.Figure()

    if not simulated_df.empty and show_cloud:
        marker_kwargs = {
            "size": 5,
            "opacity": 0.42,
            "color": "rgba(59,130,246,0.40)",
            "line": {"width": 0},
        }
        if "sharpe" in simulated_df.columns and simulated_df["sharpe"].notna().any():
            marker_kwargs = {
                "size": 5,
                "opacity": 0.52,
                "color": simulated_df["sharpe"],
                "colorscale": "Plasma",
                "colorbar": {"title": "Sharpe"},
                "line": {"width": 0},
            }

        fig.add_trace(
            go.Scatter(
                x=simulated_df["volatility"],
                y=simulated_df["return"],
                mode="markers",
                name="Portafolios simulados",
                marker=marker_kwargs,
            )
        )

    if not frontier_df.empty and show_frontier:
        frontier_line = frontier_df.sort_values("volatility").drop_duplicates(subset=["volatility"])
        fig.add_trace(
            go.Scatter(
                x=frontier_line["volatility"],
                y=frontier_line["return"],
                mode="lines",
                name="Frontera eficiente",
                line=dict(width=2.6, color="#F97316"),
            )
        )

    if show_optimal:
        mv_ret = _metric_from_block(min_var, "return", "expected_return", "retorno")
        mv_vol = _metric_from_block(min_var, "volatility", "risk", "std")
        ms_ret = _metric_from_block(max_sharpe, "return", "expected_return", "retorno")
        ms_vol = _metric_from_block(max_sharpe, "volatility", "risk", "std")

        if mv_ret is not None and mv_vol is not None:
            fig.add_trace(
                go.Scatter(
                    x=[mv_vol],
                    y=[mv_ret],
                    mode="markers",
                    name="Mínima varianza",
                    marker=dict(size=11, symbol="diamond", color="#10B981"),
                )
            )

        if ms_ret is not None and ms_vol is not None:
            fig.add_trace(
                go.Scatter(
                    x=[ms_vol],
                    y=[ms_ret],
                    mode="markers",
                    name="Máximo Sharpe",
                    marker=dict(size=13, symbol="star", color="#8B5CF6"),
                )
            )

    fig = style_plotly_figure(
        fig,
        modo=modo,
        title="",
        xaxis_title="Volatilidad",
        yaxis_title="Retorno",
        show_xgrid=not clean_view,
        show_ygrid=not clean_view,
    )
    fig.update_layout(
        margin=dict(l=24, r=24, t=26, b=24),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.12,
            xanchor="left",
            x=0.0,
            bgcolor="rgba(255,255,255,0.82)",
            bordercolor="rgba(148,163,184,0.22)",
            borderwidth=1,
            font=dict(size=10),
        ),
        plot_bgcolor="#EEF4FF" if modo == "General" else "#FBEAF1",
    )
    return fig


def _module_reading(
    min_var: dict,
    max_sharpe: dict,
    n_assets: int,
    observations,
    n_portfolios: int,
    risk_free_rate: float,
) -> str:
    mv_ret = _metric_from_block(min_var, "return", "expected_return", "retorno")
    mv_vol = _metric_from_block(min_var, "volatility", "risk", "std")
    ms_ret = _metric_from_block(max_sharpe, "return", "expected_return", "retorno")
    ms_sharpe = _metric_from_block(max_sharpe, "sharpe", "sharpe_ratio")

    return (
        f"Se analizaron {n_assets} activos con {observations} observaciones alineadas y se simularon {n_portfolios:,} "
        f"portafolios usando una tasa libre de riesgo de {_format_pct(risk_free_rate)}. "
        f"El portafolio de mínima varianza ofrece un retorno esperado de {_format_pct(mv_ret)} con volatilidad de {_format_pct(mv_vol)}, "
        f"mientras que el portafolio de máximo Sharpe alcanza un retorno esperado de {_format_pct(ms_ret)} con Sharpe de {_format_num(ms_sharpe, 3)}."
    )


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

    risk_profile_label = st.selectbox(
        "Perfil del inversor",
        ["Sin perfil", "Conservador", "Mínimo riesgo", "Máxima utilidad", "Arriesgado"],
        index=0,
        key="markowitz_investor_profile",
    )

    reference_weights, total_pct = _weights_editor(filtros_sidebar, "markowitz_weight")

risk_profile_map = {
    "Sin perfil": None,
    "Conservador": "conservador",
    "Mínimo riesgo": "minimo_riesgo",
    "Máxima utilidad": "maxima_utilidad",
    "Arriesgado": "arriesgado",
}
risk_profile = risk_profile_map[risk_profile_label]

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
    risk_free_rate=risk_free_rate,
    n_portfolios=n_portfolios,
    target_return=target_return_pct,
    risk_profile=risk_profile,
    reference_weights=reference_weights,
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
        "En modo estadístico se enfatizan la matriz de correlación, la frontera eficiente, la composición de portafolios óptimos y el perfil de inversor."
    )

if frontier_error:
    st.error(frontier_error)
    st.stop()

if not isinstance(payload, dict) or not payload:
    st.error("No se recibieron datos válidos del endpoint de optimización.")
    st.stop()

frontier_df = _extract_frontier_df(payload)
simulated_df = _extract_simulated_df(payload)
corr_df = _extract_corr_df(payload)
min_var = _extract_min_var(payload)
max_sharpe = _extract_max_sharpe(payload)
target_port = _extract_target(payload)
profile_suggestion = _extract_profile_suggestion(payload)

min_var_df = _extract_weights_df(min_var)
max_sharpe_df = _extract_weights_df(max_sharpe)
target_df = _extract_weights_df(target_port)
profile_df = _extract_weights_df(profile_suggestion)
reference_df = _extract_reference_weights_df(reference_weights)

observations = _pick_value(payload, "observations", "n_observations", "sample_size")
n_assets = _pick_value(payload, "n_assets", "num_assets") or len(BASE_PORTFOLIO)

tab1, tab2, tab3 = st.tabs(["Portafolios destacados", "Gráficas", "Composición óptima"])

with tab1:
    seccion("Portafolios destacados")

    mv_ret = _metric_from_block(min_var, "return", "expected_return", "retorno")
    mv_vol = _metric_from_block(min_var, "volatility", "risk", "std")
    ms_ret = _metric_from_block(max_sharpe, "return", "expected_return", "retorno")
    ms_sharpe = _metric_from_block(max_sharpe, "sharpe", "sharpe_ratio")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta_kpi("Retorno mín. varianza", _format_pct(mv_ret), subtexto="Rentabilidad asociada a la cartera de menor volatilidad.")
    with c2:
        tarjeta_kpi("Volatilidad mín. varianza", _format_pct(mv_vol), subtexto="Menor riesgo disponible.")
    with c3:
        tarjeta_kpi("Retorno máx. Sharpe", _format_pct(ms_ret), subtexto="Rentabilidad esperada del mejor balance riesgo-retorno.")
    with c4:
        tarjeta_kpi("Sharpe máximo", _format_num(ms_sharpe, 3), subtexto="Mejor eficiencia riesgo-retorno.")

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
        tarjeta_kpi("Activos analizados", str(int(n_assets)), subtexto="Universo usado para construir combinaciones factibles.")
    with k2:
        tarjeta_kpi("Observaciones", str(observations) if observations is not None else "N/D", subtexto="Muestra histórica disponible para covarianzas y retornos.")
    with k3:
        tarjeta_kpi("Portafolios simulados", f"{n_portfolios:,}".replace(",", "."), subtexto="Exploración aleatoria del espacio riesgo-retorno.")
    with k4:
        tarjeta_kpi("Tasa libre de riesgo", _format_pct(risk_free_rate), subtexto="Referencia para medir eficiencia ajustada por riesgo.")

    if profile_suggestion:
        p1, p2, p3 = st.columns(3)
        with p1:
            tarjeta_kpi("Perfil sugerido", str(_pick_value(profile_suggestion, "profile") or "N/D").replace("_", " ").title(), subtexto="Solución alineada al perfil seleccionado.")
        with p2:
            tarjeta_kpi("Retorno perfil", _format_pct(_metric_from_block(profile_suggestion, "return", "expected_return")), subtexto="Rentabilidad de la sugerencia.")
        with p3:
            tarjeta_kpi("Volatilidad perfil", _format_pct(_metric_from_block(profile_suggestion, "volatility", "risk")), subtexto="Riesgo de la sugerencia.")

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
            "Activo o desactiva detalles para simplificar la lectura visual de la matriz.",
            modo=modo,
            caption="Usa una escala azul-vinotinto para distinguir mejor correlaciones negativas y positivas.",
        )

        o1, o2 = st.columns(2)
        with o1:
            corr_clean = st.checkbox("Vista limpia", value=False, key="markowitz_corr_clean")
        with o2:
            show_corr_table = st.checkbox("Ver tabla de correlación", value=False, key="markowitz_corr_table")

        fig_corr = _build_corr_heatmap(corr_df, modo=modo, clean_view=corr_clean)
        st.plotly_chart(fig_corr, use_container_width=True)
        plot_card_footer(
            "La matriz de correlación ayuda a identificar qué tan parecidos son los movimientos entre activos. Correlaciones más bajas suelen mejorar el potencial de diversificación del portafolio."
        )

        if show_corr_table and not corr_df.empty:
            st.dataframe(corr_df, use_container_width=True)

    with g2:
        plot_card_header(
            "Frontera eficiente",
            "Mejoré leyenda, ejes y contraste para una lectura más clara.",
            modo=modo,
            caption="La nube simulada, la frontera y los óptimos se muestran separados visualmente para evitar interferencias con el título.",
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
            simulated_df=simulated_df,
            min_var=min_var,
            max_sharpe=max_sharpe,
            modo=modo,
            show_cloud=show_cloud,
            show_frontier=show_frontier,
            show_optimal=show_optimal,
            clean_view=frontier_clean,
        )
        st.plotly_chart(fig_frontier, use_container_width=True)
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
            "Diseñado de mayor a menor participación.",
            modo=modo,
            caption="Ordenado de mayor a menor participación.",
        )
        st.dataframe(min_var_df, use_container_width=True, hide_index=True)

    with c2:
        plot_card_header(
            "Portafolio de máximo Sharpe",
            "Diseñado de mayor a menor participación.",
            modo=modo,
            caption="Ordenado de mayor a menor participación.",
        )
        st.dataframe(max_sharpe_df, use_container_width=True, hide_index=True)

    seccion("Optimización con retorno objetivo")

    target_ret = _metric_from_block(target_port, "achieved_return_annual", "expected_return", "return", "retorno")
    target_vol = _metric_from_block(target_port, "volatility_annual", "volatility", "risk", "std")

    t1, t2 = st.columns([1.05, 1.2], gap="large")
    with t1:
        plot_card_header(
            "Solución condicionada",
            "Retorno objetivo configurado actualmente",
            modo=modo,
            caption=f"Retorno objetivo configurado actualmente: {_format_pct(target_return_pct)}",
        )
        tarjeta_kpi("Retorno esperado", _format_pct(target_ret), subtexto="Objetivo alcanzado.")
        tarjeta_kpi("Volatilidad", _format_pct(target_vol), subtexto="Riesgo asociado al retorno objetivo impuesto.")

    with t2:
        st.dataframe(target_df, use_container_width=True, hide_index=True)

    if profile_suggestion:
        seccion("Portafolio sugerido por perfil")
        s1, s2 = st.columns([1.0, 1.25], gap="large")
        with s1:
            tarjeta_kpi("Perfil", str(_pick_value(profile_suggestion, "profile") or "N/D").replace("_", " ").title(), subtexto="Preferencia seleccionada en el panel lateral.")
            tarjeta_kpi("Sharpe", _format_num(_metric_from_block(profile_suggestion, "sharpe", "sharpe_ratio"), 3), subtexto="Eficiencia de la cartera sugerida.")
        with s2:
            st.dataframe(profile_df, use_container_width=True, hide_index=True)

    seccion("Pesos de referencia del usuario")
    render_info_card(
        "Referencia visual",
        "Estos pesos son la asignación manual del usuario en el panel lateral. Sirven como referencia para comparar la cartera actual frente a las soluciones óptimas de Markowitz.",
    )
    st.dataframe(reference_df, use_container_width=True, hide_index=True)

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

    seccion("Interpretación")
    render_info_card(
        "Lectura composicional",
        "La composición óptima muestra cómo cambia el peso relativo de cada activo según el criterio elegido. Mínima varianza privilegia estabilidad, máximo Sharpe eficiencia y retorno objetivo una meta explícita de rentabilidad.",
    )