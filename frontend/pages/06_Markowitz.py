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

# --- PORTAFOLIO DINÁMICO (Conectado al Robo-Advisor) ---
if "robo_portfolio" not in st.session_state:
    st.session_state["robo_portfolio"] = [
        {"name": "Seven & i Holdings", "ticker": "3382.T", "country": "JP"},
        {"name": "Alimentation Couche-Tard", "ticker": "ATD.TO", "country": "CA"},
        {"name": "FEMSA", "ticker": "FEMSAUBD.MX", "country": "MX"},
        {"name": "BP", "ticker": "BP.L", "country": "UK"},
        {"name": "Carrefour", "ticker": "CA.PA", "country": "FR"},
    ]
CURRENT_PORTFOLIO = st.session_state["robo_portfolio"]

RF_FALLBACK_ANNUAL = 0.03
RF_FALLBACK_TICKER = "^IRX"


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


def _profile_to_backend(profile_label: str) -> str | None:
    mapping = {
        "Sin perfil": None,
        "Mínimo riesgo": "minimo_riesgo",
        "Máxima utilidad": "maxima_utilidad",
        "Arriesgado": "arriesgado",
    }
    return mapping.get(profile_label)


def _weights_editor(
    sidebar_container,
    key_prefix: str,
    disabled: bool,
) -> tuple[list[float], float]:
    with sidebar_container:
        st.markdown("**Pesos manuales del portafolio (%)**")

        if disabled:
            st.caption(
                "Los pesos manuales quedan bloqueados porque seleccionaste un perfil de optimización "
                "o un retorno objetivo. En ese caso, el backend calcula la composición óptima."
            )
        else:
            st.caption(
                "Puedes modificar estos pesos solo cuando el perfil es 'Sin perfil' y no se usa retorno objetivo."
            )

        weights_pct: list[float] = []

        for asset in CURRENT_PORTFOLIO:
            value = st.number_input(
                asset["ticker"],
                min_value=0.0,
                max_value=100.0,
                value=100.0 / len(CURRENT_PORTFOLIO) if len(CURRENT_PORTFOLIO) > 0 else 0.0,
                step=1.0,
                key=f"{key_prefix}_{asset['ticker']}",
                format="%.2f",
                disabled=disabled,
            )
            weights_pct.append(float(value))

        total_pct = float(sum(weights_pct))
        st.caption(f"Total asignado: {total_pct:.2f}%")

        if not disabled:
            if total_pct > 100.0 + 1e-6:
                st.error("Los pesos no pueden superar 100%.")
            elif abs(total_pct - 100.0) > 1e-6:
                st.warning("Los pesos manuales deberían sumar exactamente 100%.")

    return [w / 100.0 for w in weights_pct], total_pct


def _fetch_rf_usd() -> tuple[float, str, str | None]:
    client = get_api_client()

    try:
        payload = client.get_macro_snapshot(base_currency="USD")
        rf_pct = _pick_value(payload, "rf_rate_pct", "risk_free_rate_pct")
        rf_ticker = _pick_value(payload, "rf_ticker") or RF_FALLBACK_TICKER

        if rf_pct is None:
            return RF_FALLBACK_ANNUAL, RF_FALLBACK_TICKER, "El backend no devolvió Rf; se usó fallback 3%."

        return float(rf_pct) / 100.0, str(rf_ticker), None
    except Exception as exc:
        return RF_FALLBACK_ANNUAL, RF_FALLBACK_TICKER, f"No fue posible consultar Rf desde backend: {exc}"


def _build_frontier_payload(
    start: str,
    end: str,
    risk_free_rate: float,
    n_portfolios: int,
    target_return: float | None,
    risk_profile: str | None,
) -> dict:
    return {
        "tickers": [a["ticker"] for a in CURRENT_PORTFOLIO],
        "start": start,
        "end": end,
        "rf_annual": risk_free_rate,
        "n_portfolios": n_portfolios,
        "target_return_annual": target_return,
        "risk_profile": risk_profile,
        "return_type": "log",
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
    for asset, weight in zip(CURRENT_PORTFOLIO, weights):
        rows.append(
            {
                "Activo": asset["ticker"],
                "Peso": float(weight),
                "Participación": f"{float(weight):.2%}",
            }
        )
    return pd.DataFrame(rows).sort_values("Peso", ascending=False).reset_index(drop=True)



def _extract_top_portfolios_df(payload: dict) -> pd.DataFrame:
    top_portfolios = payload.get("top_portfolios", [])

    if not isinstance(top_portfolios, list) or not top_portfolios:
        return pd.DataFrame()

    rows = []

    for item in top_portfolios:
        weights = item.get("weights", [])
        weights_text = ""

        if isinstance(weights, list):
            weights_text = " | ".join(
                [
                    f"{w.get('asset', 'N/D')}: {float(w.get('weight', 0)):.2%}"
                    for w in weights
                    if isinstance(w, dict)
                ]
            )

        rows.append(
            {
                "Ranking": item.get("rank"),
                "Retorno esperado": _format_pct(item.get("return")),
                "Volatilidad": _format_pct(item.get("volatility")),
                "Sharpe": _format_num(item.get("sharpe"), 3),
                "Pesos": weights_text,
            }
        )

    return pd.DataFrame(rows)


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


def _selected_portfolio_block(
    profile_label: str,
    use_target_return: bool,
    min_var: dict,
    max_sharpe: dict,
    target_port: dict,
    profile_suggestion: dict,
) -> tuple[str, dict]:
    if use_target_return and target_port:
        return "Portafolio por retorno objetivo", target_port

    if profile_label == "Mínimo riesgo" and min_var:
        return "Portafolio de mínimo riesgo", min_var

    if profile_label == "Máxima utilidad" and max_sharpe:
        return "Portafolio de máxima utilidad", max_sharpe

    if profile_label == "Arriesgado" and profile_suggestion:
        return "Portafolio sugerido para perfil arriesgado", profile_suggestion

    if profile_label == "Arriesgado" and max_sharpe:
        return "Portafolio arriesgado aproximado", max_sharpe

    if max_sharpe:
        return "Portafolio de referencia: máximo Sharpe", max_sharpe

    return "Portafolio seleccionado", {}


def _selected_return_and_vol(block: dict) -> tuple[float | None, float | None]:
    ret = _metric_from_block(
        block,
        "achieved_return_annual",
        "return",
        "expected_return",
        "retorno",
    )
    vol = _metric_from_block(
        block,
        "volatility_annual",
        "volatility",
        "risk",
        "std",
    )
    return ret, vol


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
    selected_block: dict,
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
        sel_ret, sel_vol = _selected_return_and_vol(selected_block)

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

        if sel_ret is not None and sel_vol is not None:
            fig.add_trace(
                go.Scatter(
                    x=[sel_vol],
                    y=[sel_ret],
                    mode="markers",
                    name="Seleccionado",
                    marker=dict(size=14, symbol="circle", color="#DC2626"),
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
    selected_label: str,
    selected_block: dict,
    n_assets: int,
    observations,
    n_portfolios: int,
    risk_free_rate: float,
) -> str:
    mv_ret = _metric_from_block(min_var, "return", "expected_return", "retorno")
    mv_vol = _metric_from_block(min_var, "volatility", "risk", "std")
    ms_ret = _metric_from_block(max_sharpe, "return", "expected_return", "retorno")
    ms_sharpe = _metric_from_block(max_sharpe, "sharpe", "sharpe_ratio")
    sel_ret, sel_vol = _selected_return_and_vol(selected_block)

    return (
        f"Se analizaron {n_assets} activos con {observations} observaciones alineadas y se simularon "
        f"{n_portfolios:,} portafolios usando una tasa libre de riesgo metodológica de {_format_pct(risk_free_rate)}. "
        f"El portafolio de mínima varianza ofrece un retorno esperado de {_format_pct(mv_ret)} con volatilidad de {_format_pct(mv_vol)}, "
        f"mientras que el portafolio de máximo Sharpe alcanza un retorno esperado de {_format_pct(ms_ret)} con Sharpe de {_format_num(ms_sharpe, 3)}. "
        f"La selección actual es '{selected_label}', con retorno esperado de {_format_pct(sel_ret)} y volatilidad de {_format_pct(sel_vol)}."
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

    portfolio_value = st.number_input(
        "Valor del portafolio",
        min_value=1000.0,
        max_value=100000000.0,
        value=100000.0,
        step=1000.0,
        key="markowitz_portfolio_value",
        format="%.2f",
        help="Monto que el inversionista desea invertir. Se usa para convertir retornos esperados porcentuales a valores monetarios.",
    )

    n_portfolios = st.slider(
        "Número de portafolios",
        min_value=10000,
        max_value=50000,
        value=10000,
        step=1000,
        key="markowitz_n_portfolios",
        help="Cantidad de combinaciones simuladas para construir la nube de portafolios y la frontera eficiente.",
    )

    risk_profile_label = st.selectbox(
        "Perfil del inversor",
        ["Sin perfil", "Mínimo riesgo", "Máxima utilidad", "Arriesgado"],
        index=0,
        key="markowitz_investor_profile",
        help=(
            "Sin perfil permite editar pesos manualmente. "
            "Mínimo riesgo, Máxima utilidad y Arriesgado usan pesos sugeridos por el modelo."
        ),
    )

    use_target_return = st.checkbox(
        "Usar retorno objetivo",
        value=False,
        key="markowitz_use_target_return",
        help="Si activas esta opción, los pesos manuales se bloquean porque el modelo busca el portafolio más cercano al retorno deseado.",
    )

    target_return_pct = None
    if use_target_return:
        target_return_pct = (
            st.number_input(
                "Retorno anual objetivo (%)",
                min_value=0.0,
                max_value=50.0,
                value=10.0,
                step=0.5,
                key="markowitz_target_return",
                format="%.2f",
            )
            / 100.0
        )

    allow_manual_weights = risk_profile_label == "Sin perfil" and not use_target_return

    reference_weights, total_pct = _weights_editor(
        filtros_sidebar,
        "markowitz_weight",
        disabled=not allow_manual_weights,
    )

    # --- LÓGICA DEL ROBO-ADVISOR HÍBRIDO ---
    st.markdown("---")
    st.subheader("🤖 Perri - Robo-Advisor Cuantitativo")
    
    num_sugeridos = st.slider("Activos totales deseados", 2, 15, 5, key="robo_num_assets", help="¿De cuántos activos quieres el portafolio final?")
    
    if st.button("Generar sugerencia con Perri", use_container_width=True):
        with st.spinner("Consultando reserva institucional y optimizando..."):
            try:
                client = get_api_client()
                
                # Mapeo del perfil del selectbox al formato del backend
                robo_profile_map = {
                    "Sin perfil": "moderado",
                    "Mínimo riesgo": "conservador",
                    "Máxima utilidad": "moderado",
                    "Arriesgado": "agresivo"
                }
                robo_profile = robo_profile_map.get(risk_profile_label, "moderado")
                
                # Preparamos la petición al backend
                payload = {
                    "profile": robo_profile,
                    "total_assets": num_sugeridos,
                    "custom_tickers": [a["ticker"] for a in CURRENT_PORTFOLIO]
                }
                
                # Llamamos al nuevo endpoint
                response = client.post_roboadvisor_suggest(payload)
                
                if response and "tickers" in response:
                    st.success("¡Portafolio híbrido generado!")
                    # Convertimos los tickers devueltos al formato que usa la página
                    st.session_state["robo_portfolio"] = [
                        {"name": t, "ticker": t, "country": "IA"} for t in response["tickers"]
                    ]
                    # Forzamos recarga para que dibuje el dashboard con los nuevos activos
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error de conexión con la IA: {str(e)}")

risk_profile = _profile_to_backend(risk_profile_label)

start_date, end_date = _resolve_dates(
    horizonte=horizonte,
    default_end=today,
    custom_start=pd.Timestamp(custom_start) if custom_start is not None else None,
    custom_end=pd.Timestamp(custom_end) if custom_end is not None else None,
)

if start_date >= end_date:
    st.error("La fecha inicial debe ser menor que la fecha final.")
    st.stop()

rf_annual, rf_ticker, rf_warning = _fetch_rf_usd()

request_payload = _build_frontier_payload(
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
    risk_free_rate=rf_annual,
    n_portfolios=n_portfolios,
    target_return=target_return_pct,
    risk_profile=risk_profile,
)

payload, frontier_error = _fetch_frontier(request_payload)

header_dashboard(
    "Módulo 6 - Markowitz",
    "Construye y compara carteras sobre la frontera eficiente para estudiar riesgo, retorno, eficiencia y composición óptima",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo construye múltiples combinaciones de portafolios para identificar aquellas que ofrecen una mejor relación entre retorno esperado y riesgo. "
        "La tasa libre de riesgo no es editable: se toma desde la metodología del proyecto en USD."
    )
else:
    nota(
        "En modo estadístico se enfatizan la matriz de correlación, la frontera eficiente, la composición de portafolios óptimos, "
        "la tasa libre de riesgo metodológica y el perfil del inversionista."
    )

if rf_warning:
    st.warning(rf_warning)

if allow_manual_weights and abs(total_pct - 100.0) > 1e-6:
    st.error("Cuando usas pesos manuales, estos deben sumar exactamente 100%.")
    st.stop()

if frontier_error:
    st.error(frontier_error)
    st.stop()

if not isinstance(payload, dict) or not payload:
    st.error("No se recibieron datos válidos del endpoint de optimización.")
    st.stop()

frontier_df = _extract_frontier_df(payload)
simulated_df = _extract_simulated_df(payload)
top_portfolios_df = _extract_top_portfolios_df(payload)
corr_df = _extract_corr_df(payload)
min_var = _extract_min_var(payload)
max_sharpe = _extract_max_sharpe(payload)
target_port = _extract_target(payload)
profile_suggestion = _extract_profile_suggestion(payload)

max_sharpe_return = _metric_from_block(
    max_sharpe,
    "return",
    "expected_return",
    "retorno",
)

if (
    use_target_return
    and target_return_pct is not None
    and max_sharpe_return is not None
    and float(target_return_pct) > float(max_sharpe_return)
):
    st.error(
        "Excede las capacidades de este portafolio. "
        f"El retorno anual objetivo ingresado es {_format_pct(target_return_pct)}, "
        f"pero el portafolio de máxima utilidad alcanza aproximadamente {_format_pct(max_sharpe_return)}."
    )
    st.stop()   

selected_label, selected_block = _selected_portfolio_block(
    profile_label=risk_profile_label,
    use_target_return=use_target_return,
    min_var=min_var,
    max_sharpe=max_sharpe,
    target_port=target_port,
    profile_suggestion=profile_suggestion,
)

selected_return, selected_volatility = _selected_return_and_vol(selected_block)
selected_money_return = None if selected_return is None else portfolio_value * float(selected_return)
selected_final_value = None if selected_return is None else portfolio_value * (1.0 + float(selected_return))

min_var_df = _extract_weights_df(min_var)
max_sharpe_df = _extract_weights_df(max_sharpe)
target_df = _extract_weights_df(target_port)
profile_df = _extract_weights_df(profile_suggestion)
selected_df = _extract_weights_df(selected_block)
reference_df = _extract_reference_weights_df(reference_weights)

observations = _pick_value(payload, "observations", "n_observations", "sample_size")
n_assets = _pick_value(payload, "n_assets", "num_assets") or len(CURRENT_PORTFOLIO)

render_meta_row(
    [
        ("Horizonte", horizonte),
        ("Perfil", risk_profile_label),
        ("Retorno objetivo", _format_pct(target_return_pct) if use_target_return else "No usado"),
        ("Rf metodológica", f"{rf_ticker} · {_format_pct(rf_annual)}"),
        ("Valor portafolio", _format_money(portfolio_value)),
    ]
)

tab1, tab2, tab3 = st.tabs(["Portafolios destacados", "Gráficas", "Composición óptima"])

with tab1:
    seccion("Portafolio seleccionado")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tarjeta_kpi(
            "Selección actual",
            selected_label,
            subtexto="Criterio usado para elegir la cartera mostrada.",
            help_text="Depende del perfil del inversor o del retorno objetivo activado.",
        )

    with c2:
        tarjeta_kpi(
            "Retorno esperado",
            _format_pct(selected_return),
            subtexto="Rentabilidad anual esperada del portafolio seleccionado.",
            help_text="Retorno anual estimado para la cartera elegida dentro de las simulaciones.",
        )

    with c3:
        tarjeta_kpi(
            "Volatilidad",
            _format_pct(selected_volatility),
            subtexto="Riesgo anual asociado a la cartera seleccionada.",
            help_text="La volatilidad resume la dispersión esperada del rendimiento anual.",
        )

    with c4:
        tarjeta_kpi(
            "Valor final esperado",
            _format_money(selected_final_value),
            subtexto="Valor aproximado si se cumple el retorno esperado.",
            help_text="Valor final esperado = valor inicial del portafolio multiplicado por 1 + retorno esperado.",
        )

    k5, k6 = st.columns(2)

    with k5:
        tarjeta_kpi(
            "Retorno esperado en dinero",
            _format_money(selected_money_return),
            subtexto="Ganancia o pérdida esperada en USD.",
            help_text="Retorno monetario = valor del portafolio multiplicado por el retorno esperado.",
        )

    with k6:
        tarjeta_kpi(
            "Tasa libre de riesgo",
            _format_pct(rf_annual),
            subtexto=f"Fuente metodológica: {rf_ticker}.",
            help_text="La tasa libre de riesgo se usa para calcular Sharpe y comparar eficiencia riesgo-retorno.",
        )

    plot_card_footer(
        _module_reading(
            min_var=min_var,
            max_sharpe=max_sharpe,
            selected_label=selected_label,
            selected_block=selected_block,
            n_assets=int(n_assets),
            observations=observations,
            n_portfolios=n_portfolios,
            risk_free_rate=rf_annual,
        )
    )

    seccion("Portafolios destacados")

    mv_ret = _metric_from_block(min_var, "return", "expected_return", "retorno")
    mv_vol = _metric_from_block(min_var, "volatility", "risk", "std")
    ms_ret = _metric_from_block(max_sharpe, "return", "expected_return", "retorno")
    ms_sharpe = _metric_from_block(max_sharpe, "sharpe", "sharpe_ratio")

    p1, p2, p3, p4 = st.columns(4)

    with p1:
        tarjeta_kpi(
            "Retorno mín. varianza",
            _format_pct(mv_ret),
            subtexto="Rentabilidad asociada a la cartera de menor volatilidad.",
        )

    with p2:
        tarjeta_kpi(
            "Volatilidad mín. varianza",
            _format_pct(mv_vol),
            subtexto="Menor riesgo disponible dentro de la simulación.",
        )

    with p3:
        tarjeta_kpi(
            "Retorno máx. Sharpe",
            _format_pct(ms_ret),
            subtexto="Rentabilidad esperada del mejor balance riesgo-retorno.",
        )

    with p4:
        tarjeta_kpi(
            "Sharpe máximo",
            _format_num(ms_sharpe, 3),
            subtexto="Mejor eficiencia riesgo-retorno.",
        )

    seccion("Top 5 portafolios por Sharpe")

    if top_portfolios_df.empty:
        render_info_card(
            "Ranking no disponible",
            "El backend no devolvió el ranking de mejores portafolios para esta simulación.",
        )
    else:
        st.dataframe(
            top_portfolios_df,
            width="stretch",
            hide_index=True,
        )

        render_info_card(
            "Lectura del ranking",
            (
                "Este ranking muestra las cinco combinaciones simuladas con mejor relación riesgo-retorno, "
                "ordenadas por ratio de Sharpe. No reemplaza el portafolio de máximo Sharpe calculado por optimización, "
                "pero sirve como comparación práctica entre alternativas cercanas."
            ),
        )

    seccion("KPIs del módulo")

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        tarjeta_kpi(
            "Activos analizados",
            str(int(n_assets)),
            subtexto="Universo usado para construir combinaciones factibles.",
        )

    with k2:
        tarjeta_kpi(
            "Observaciones",
            str(observations) if observations is not None else "N/D",
            subtexto="Muestra histórica disponible para covarianzas y retornos.",
        )

    with k3:
        tarjeta_kpi(
            "Portafolios simulados",
            f"{n_portfolios:,}".replace(",", "."),
            subtexto="Exploración aleatoria del espacio riesgo-retorno.",
        )

    with k4:
        tarjeta_kpi(
            "Rf usada",
            _format_pct(rf_annual),
            subtexto=f"Ticker de referencia: {rf_ticker}.",
        )

    seccion("Interpretación")

    render_info_card(
        "Lectura del módulo",
        (
            "Este módulo muestra que no existe una única mejor cartera: todo depende del equilibrio entre retorno y riesgo. "
            "La frontera eficiente resume las combinaciones más convenientes, mientras que mínima varianza, máximo Sharpe, perfil del inversor "
            "y retorno objetivo representan decisiones distintas dentro del mismo problema."
        ),
    )

    render_info_card(
        "Regla de pesos",
        (
            "Los pesos manuales solo se habilitan cuando el perfil es 'Sin perfil' y no se usa retorno objetivo. "
            "Cuando eliges un perfil o un retorno objetivo, los pesos se bloquean porque la composición debe salir del modelo de optimización."
        ),
    )

with tab2:
    seccion("Visualizaciones de optimización")

    g1, g2 = st.columns(2, gap="large")

    with g1:
        plot_card_header(
            "Matriz de correlación",
            "La matriz de correlación muestra qué tan parecido se mueven los activos entre sí. Correlaciones más bajas ayudan a diversificar.",
            modo=modo,
            caption="Usa una escala azul-vinotinto para distinguir correlaciones negativas y positivas.",
        )

        o1, o2 = st.columns(2)
        with o1:
            corr_clean = st.checkbox("Vista limpia", value=False, key="markowitz_corr_clean")
        with o2:
            show_corr_table = st.checkbox("Ver tabla de correlación", value=False, key="markowitz_corr_table")

        fig_corr = _build_corr_heatmap(corr_df, modo=modo, clean_view=corr_clean)
        st.plotly_chart(fig_corr, width="stretch")
        plot_card_footer(
            "La matriz de correlación ayuda a identificar qué activos se mueven parecido y cuáles aportan diversificación."
        )

        if show_corr_table and not corr_df.empty:
            st.dataframe(corr_df, width="stretch")

    with g2:
        plot_card_header(
            "Frontera eficiente",
            "La frontera eficiente muestra las combinaciones que maximizan retorno para cada nivel de riesgo.",
            modo=modo,
            caption="La nube simulada, la frontera, los óptimos y la selección actual se muestran diferenciados.",
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
            selected_block=selected_block,
            modo=modo,
            show_cloud=show_cloud,
            show_frontier=show_frontier,
            show_optimal=show_optimal,
            clean_view=frontier_clean,
        )
        st.plotly_chart(fig_frontier, width="stretch")
        plot_card_footer(
            "La frontera eficiente resume las mejores combinaciones riesgo-retorno encontradas. "
            "El punto seleccionado depende del perfil o del retorno objetivo configurado."
        )

    seccion("Interpretación gráfica")

    render_info_card(
        "Lectura gráfica",
        (
            "La dispersión de portafolios permite ver el trade-off entre riesgo y retorno. "
            "La curva eficiente concentra las soluciones dominantes, mientras que la matriz de correlación explica "
            "por qué ciertas combinaciones ofrecen más diversificación que otras."
        ),
    )

with tab3:
    seccion("Composición del portafolio seleccionado")

    plot_card_header(
        selected_label,
        "La composición muestra los pesos que el modelo asigna al portafolio seleccionado.",
        modo=modo,
        caption="Ordenado de mayor a menor participación.",
    )

    if selected_df.empty:
        render_info_card(
            "Sin composición disponible",
            "El backend no devolvió pesos para el portafolio seleccionado.",
        )
    else:
        st.dataframe(selected_df, width="stretch", hide_index=True)

    seccion("Composición de portafolios óptimos")

    c1, c2 = st.columns(2, gap="large")

    with c1:
        plot_card_header(
            "Portafolio de mínima varianza",
            "Cartera con menor volatilidad simulada.",
            modo=modo,
            caption="Ordenado de mayor a menor participación.",
        )
        st.dataframe(min_var_df, width="stretch", hide_index=True)

    with c2:
        plot_card_header(
            "Portafolio de máximo Sharpe",
            "Cartera con mejor relación entre exceso de retorno y riesgo.",
            modo=modo,
            caption="Ordenado de mayor a menor participación.",
        )
        st.dataframe(max_sharpe_df, width="stretch", hide_index=True)

    if use_target_return:
        seccion("Optimización con retorno objetivo")

        target_ret = _metric_from_block(
            target_port,
            "achieved_return_annual",
            "expected_return",
            "return",
            "retorno",
        )
        target_vol = _metric_from_block(
            target_port,
            "volatility_annual",
            "volatility",
            "risk",
            "std",
        )

        t1, t2 = st.columns([1.05, 1.2], gap="large")

        with t1:
            plot_card_header(
                "Solución condicionada",
                "Portafolio más cercano al retorno objetivo configurado.",
                modo=modo,
                caption=f"Retorno objetivo configurado: {_format_pct(target_return_pct)}",
            )
            tarjeta_kpi("Retorno esperado", _format_pct(target_ret), subtexto="Objetivo alcanzado.")
            tarjeta_kpi("Volatilidad", _format_pct(target_vol), subtexto="Riesgo asociado al retorno objetivo.")

        with t2:
            st.dataframe(target_df, width="stretch", hide_index=True)

    if profile_suggestion:
        seccion("Portafolio sugerido por perfil")

        s1, s2 = st.columns([1.0, 1.25], gap="large")

        with s1:
            tarjeta_kpi(
                "Perfil",
                str(_pick_value(profile_suggestion, "profile") or "N/D").replace("_", " ").title(),
                subtexto="Preferencia seleccionada en el panel lateral.",
            )
            tarjeta_kpi(
                "Sharpe",
                _format_num(_metric_from_block(profile_suggestion, "sharpe", "sharpe_ratio"), 3),
                subtexto="Eficiencia de la cartera sugerida.",
            )

        with s2:
            st.dataframe(profile_df, width="stretch", hide_index=True)

    seccion("Pesos manuales de referencia")

    render_info_card(
        "Referencia manual",
        (
            "Estos pesos solo son editables cuando el perfil es 'Sin perfil' y no se usa retorno objetivo. "
            "Cuando el usuario elige un perfil o un retorno objetivo, la composición relevante es la que calcula el backend."
        ),
    )

    st.dataframe(reference_df, width="stretch", hide_index=True)

    seccion("Interpretación")

    render_info_card(
        "Lectura composicional",
        (
            "La composición óptima muestra cómo cambia el peso relativo de cada activo según el criterio elegido. "
            "Mínima varianza privilegia estabilidad, máximo Sharpe privilegia eficiencia, retorno objetivo busca una meta explícita "
            "y el perfil arriesgado prioriza una cartera con mayor expectativa de retorno."
        ),
    )