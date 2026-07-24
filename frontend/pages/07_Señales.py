from __future__ import annotations

import html
import math
import pandas as pd
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
from ui.portfolio_state import (
    HORIZON_OPTIONS,
    active_assets,
    active_custom_dates,
    horizon_index,
    render_portfolio_scope_note,
)


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


def _safe_str(v) -> str:
    if v is None:
        return "N/D"
    return str(v)


def _safe_float(v) -> float | None:
    try:
        if v is None:
            return None
        f = float(v)
        if math.isnan(f):
            return None
        return f
    except Exception:
        return None


def _pick_value(payload: dict | None, *keys):
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _extract_alert_items(payload: dict) -> list[dict]:
    for key in ["alerts", "items", "signals", "data", "results"]:
        val = payload.get(key)
        if isinstance(val, list):
            return val
    if isinstance(payload, dict) and payload:
        return [payload]
    return []


def _fetch_alerts_for_asset(
    ticker: str,
    start: str,
    end: str,
    rsi_overbought: float,
    rsi_oversold: float,
    stoch_overbought: float,
    stoch_oversold: float,
    sma_short_window: int,
    sma_long_window: int,
) -> tuple[dict, str | None]:
    client = get_api_client()
    try:
        payload = client.get_alerts(
            ticker=ticker,
            start=start,
            end=end,
            rsi_overbought=rsi_overbought,
            rsi_oversold=rsi_oversold,
            stoch_overbought=stoch_overbought,
            stoch_oversold=stoch_oversold,
            sma_short_window=sma_short_window,
            sma_long_window=sma_long_window,
        )
        if not isinstance(payload, dict):
            return {}, f"Respuesta no válida para {ticker}: {type(payload).__name__}"
        return payload, None
    except ApiClientError as exc:
        return {}, exc.message
    except Exception as exc:
        return {}, f"Error inesperado consultando señales para {ticker}: {exc}"


def _infer_signal_status(alert: dict) -> tuple[str, str, str]:
    action = _safe_str(_pick_value(alert, "signal", "action", "status", "state")).lower()
    title = _safe_str(_pick_value(alert, "title", "name", "indicator", "type")).lower()

    if any(x in action for x in ["buy", "compra", "bull", "alcista", "golden_cross"]):
        return "Compra", "#15803D", "#DCFCE7"
    if any(x in action for x in ["sell", "venta", "bear", "bajista", "death_cross"]):
        return "Venta", "#B91C1C", "#FEE2E2"
    if any(x in action for x in ["neutral", "hold", "espera", "sin_senal", "sin señal"]):
        return "Neutral", "#475569", "#E2E8F0"

    if "sobrecompra" in title:
        return "Venta", "#B91C1C", "#FEE2E2"
    if "sobreventa" in title:
        return "Compra", "#15803D", "#DCFCE7"

    return "Neutral", "#475569", "#E2E8F0"


def _human_title(alert: dict) -> str:
    title = _pick_value(alert, "title", "name", "indicator", "type", "signal_name")
    if title:
        return str(title)

    category = _safe_str(_pick_value(alert, "category", "source")).lower()
    if "macd" in category:
        return "MACD"
    if "rsi" in category:
        return "RSI"
    if "boll" in category:
        return "Bollinger"
    if "stoch" in category:
        return "Stochastic"
    if "moving" in category or "media" in category:
        return "Moving Averages"
    return "Señal técnica"


def _human_description(alert: dict) -> str:
    title = _human_title(alert).lower()
    category = _safe_str(_pick_value(alert, "category", "source", "indicator", "type")).lower()
    joined = f"{title} {category}".lower()

    if "macd" in joined:
        return "Cruce entre MACD y su línea de señal; resume cambios de momentum."
    if "rsi" in joined:
        return "RSI en zona extrema: sobrecompra o sobreventa según los umbrales configurados."
    if "boll" in joined:
        return "Precio cercano o por fuera de las bandas de Bollinger; indica presión o dispersión elevada."
    if "stoch" in joined or "estoc" in joined:
        return "Lectura del Estocástico %K/%D en zonas extremas de corto plazo."
    if "moving" in joined or "media" in joined:
        return "Cruce de medias móviles; resume cambios en la dirección de tendencia."
    return "Condición técnica detectada por el backend según los indicadores configurados."


def _human_date(alert: dict) -> str:
    for key in ["date", "timestamp", "observed_at", "signal_date", "last_date"]:
        value = _pick_value(alert, key)
        if value:
            return str(value)
    return "Sin evento fechado"


def _human_value(alert: dict) -> str:
    value = _pick_value(alert, "value", "indicator_value", "last_value", "reading")
    if value is None:
        return "N/D"
    f = _safe_float(value)
    if f is None:
        return str(value)
    return f"{f:.2f}"


def _render_signal_card(alert: dict):
    status, badge_color, badge_bg = _infer_signal_status(alert)
    title = _human_title(alert)
    description = _safe_str(_pick_value(alert, "signal", "action", "state")).replace("_", " ").title()
    signal_date = _safe_str(_pick_value(alert, "rule", "category", "source")).replace("_", " ").title()
    signal_value = _human_value(alert)

    accent = {
        "Compra": "#15803D",
        "Venta": "#B91C1C",
        "Neutral": "#64748B",
    }.get(status, "#64748B")

    soft_bg = {
        "Compra": "linear-gradient(180deg, #F0FDF4 0%, #FFFFFF 100%)",
        "Venta": "linear-gradient(180deg, #FEF2F2 0%, #FFFFFF 100%)",
        "Neutral": "linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 100%)",
    }.get(status, "linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 100%)")

    icon = {
        "Compra": "🟢",
        "Venta": "🔴",
        "Neutral": "🟡",
    }.get(status, "🟡")

    icon = "*"

    card_html = f"""
    <div style="
        background: {soft_bg};
        border: 1px solid rgba(148,163,184,0.18);
        border-left: 6px solid {accent};
        border-radius: 20px;
        box-shadow: 0 14px 28px rgba(15,23,42,0.07);
        padding: 1rem 1rem 1rem 1rem;
        min-height: 170px;
        font-family: Arial, sans-serif;
    ">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:0.75rem;margin-bottom:0.8rem;">
            <div style="display:flex;align-items:center;gap:0.55rem;">
                <div style="font-size:1.05rem;">{icon}</div>
                <div style="font-size:1rem;font-weight:800;color:#0F172A;">
                    {title}
                </div>
            </div>
            <div style="
                padding:0.32rem 0.72rem;
                border-radius:999px;
                background:{badge_bg};
                color:{badge_color};
                border:1px solid {badge_color}30;
                font-size:0.76rem;
                font-weight:900;
                letter-spacing:0;
                text-transform:uppercase;
            ">
                {status}
            </div>
        </div>

        <div style="
            font-size:0.90rem;
            font-weight:700;
            color:#334155;
            margin-bottom:0.85rem;
            line-height:1.5;
        ">
            {description}
        </div>

        <div style="
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:0.75rem;
            margin-bottom:0.9rem;
        ">
            <div style="
                background: rgba(255,255,255,0.78);
                border: 1px solid rgba(148,163,184,0.16);
                border-radius: 14px;
                padding: 0.65rem 0.75rem;
            ">
                <div style="font-size:0.74rem;color:#64748B;font-weight:800;text-transform:uppercase;letter-spacing:0;">
                    Regla
                </div>
                <div style="font-size:0.86rem;color:#0F172A;font-weight:700;margin-top:0.18rem;">
                    {signal_date}
                </div>
            </div>

            <div style="
                background: rgba(255,255,255,0.78);
                border: 1px solid rgba(148,163,184,0.16);
                border-radius: 14px;
                padding: 0.65rem 0.75rem;
            ">
                <div style="font-size:0.74rem;color:#64748B;font-weight:800;text-transform:uppercase;letter-spacing:0;">
                    Valor
                </div>
                <div style="font-size:0.86rem;color:#0F172A;font-weight:700;margin-top:0.18rem;">
                    {signal_value}
                </div>
            </div>
        </div>

        <div style="
            padding:0.70rem 0.78rem;
            border-radius:14px;
            background: rgba(255,255,255,0.82);
            border:1px solid rgba(148,163,184,0.14);
            font-size:0.90rem;
            line-height:1.5;
            color:#334155;
            font-weight:600;
        ">
            Estado: <span style="color:{accent};font-weight:800;">{status.lower()}</span>
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def _build_summary_rows(asset_results: list[dict]) -> pd.DataFrame:
    rows = []
    for item in asset_results:
        alerts = item.get("alerts", [])
        n_buy = 0
        n_sell = 0
        n_neutral = 0

        for alert in alerts:
            status, _, _ = _infer_signal_status(alert)
            if status == "Compra":
                n_buy += 1
            elif status == "Venta":
                n_sell += 1
            else:
                n_neutral += 1

        rows.append(
            {
                "Activo": item["ticker"],
                "Compra": n_buy,
                "Venta": n_sell,
                "Neutral": n_neutral,
                "Total": len(alerts),
            }
        )

    return pd.DataFrame(rows)


def _clean_label(value) -> str:
    return html.escape(_safe_str(value).replace("_", " ").strip().title())


def _render_signal_card(alert: dict):
    status, badge_color, badge_bg = _infer_signal_status(alert)
    title = html.escape(_human_title(alert))
    description = html.escape(_human_description(alert))
    rule = _clean_label(_pick_value(alert, "rule", "category", "source", "indicator", "type"))
    signal_date = html.escape(_human_date(alert))
    signal_value = html.escape(_human_value(alert))

    accent = {
        "Compra": "#0F8A4B",
        "Venta": "#B42318",
        "Neutral": "#52606D",
    }.get(status, "#52606D")

    st.markdown(
        f"""
        <div class="signal-card" style="--accent:{accent}; --badge:{badge_color}; --badge-bg:{badge_bg};">
            <div class="signal-card__top">
                <div>
                    <div class="signal-card__eyebrow">{rule}</div>
                    <div class="signal-card__title">{title}</div>
                </div>
                <span class="signal-card__badge">{html.escape(status.upper())}</span>
            </div>
            <div class="signal-card__body">{description}</div>
            <div class="signal-card__meta">
                <div>
                    <span>Fecha</span>
                    <strong>{signal_date}</strong>
                </div>
                <div>
                    <span>Valor</span>
                    <strong>{signal_value}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _signal_counts(alerts: list[dict]) -> tuple[int, int, int]:
    counts = {"Compra": 0, "Venta": 0, "Neutral": 0}
    for alert in alerts:
        status, _, _ = _infer_signal_status(alert)
        counts[status] = counts.get(status, 0) + 1
    return counts["Compra"], counts["Venta"], counts["Neutral"]


def _render_asset_signal_header(item: dict):
    alerts = item.get("alerts", [])
    n_buy, n_sell, n_neutral = _signal_counts(alerts)
    title = html.escape(f"{item['name']} ({item['ticker']})")

    st.markdown(
        f"""
        <div class="signal-asset-header">
            <div>
                <div class="signal-asset-header__label">Activo monitoreado</div>
                <div class="signal-asset-header__title">{title}</div>
            </div>
            <div class="signal-asset-header__counts">
                <span class="is-buy">{n_buy} compra</span>
                <span class="is-sell">{n_sell} venta</span>
                <span class="is-neutral">{n_neutral} neutral</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _inject_signal_styles():
    st.markdown(
        """
        <style>
        .signal-asset-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin: 1.15rem 0 0.75rem;
            padding: 0.95rem 1rem;
            border: 1px solid rgba(15, 23, 42, 0.10);
            border-radius: 8px;
            background: #FFFFFF;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
        }
        .signal-asset-header__label {
            color: #64748B;
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
        }
        .signal-asset-header__title {
            color: #0F172A;
            font-size: 1.02rem;
            font-weight: 850;
            margin-top: 0.1rem;
        }
        .signal-asset-header__counts {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            justify-content: flex-end;
        }
        .signal-asset-header__counts span,
        .signal-card__badge {
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 850;
            padding: 0.34rem 0.62rem;
            white-space: nowrap;
        }
        .is-buy { background: #EAFBF1; color: #0F8A4B; }
        .is-sell { background: #FFF0EE; color: #B42318; }
        .is-neutral { background: #EEF2F6; color: #52606D; }
        .signal-card {
            min-height: 180px;
            margin-bottom: 0.9rem;
            padding: 1rem;
            border: 1px solid rgba(15, 23, 42, 0.10);
            border-left: 5px solid var(--accent);
            border-radius: 8px;
            background: #FFFFFF;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        }
        .signal-card__top {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 0.75rem;
        }
        .signal-card__eyebrow {
            color: #64748B;
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
        }
        .signal-card__title {
            color: #0F172A;
            font-size: 1rem;
            font-weight: 850;
            line-height: 1.25;
            margin-top: 0.12rem;
        }
        .signal-card__badge {
            background: var(--badge-bg);
            color: var(--badge);
            border: 1px solid color-mix(in srgb, var(--badge) 20%, transparent);
        }
        .signal-card__body {
            color: #334155;
            font-size: 0.9rem;
            font-weight: 600;
            line-height: 1.45;
            min-height: 3.8rem;
        }
        .signal-card__meta {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.55rem;
            margin-top: 0.85rem;
        }
        .signal-card__meta div {
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 8px;
            padding: 0.58rem 0.65rem;
            background: #F8FAFC;
        }
        .signal-card__meta span {
            display: block;
            color: #64748B;
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
        }
        .signal-card__meta strong {
            display: block;
            color: #0F172A;
            font-size: 0.86rem;
            margin-top: 0.12rem;
        }
        @media (max-width: 760px) {
            .signal-asset-header {
                align-items: flex-start;
                flex-direction: column;
            }
            .signal-asset-header__counts {
                justify-content: flex-start;
            }
            .signal-card__top {
                flex-direction: column;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


modo, filtros_sidebar = setup_dashboard_page(
    title="P.R.ED",
    subtitle="Desarrolla Tus Portafolios",
    modo_default="General",
    filtros_label="Parámetros de Señales",
    filtros_expanded=False,
)

today = pd.Timestamp.today().normalize()
portfolio_assets = active_assets() or BASE_PORTFOLIO
stored_custom_start, stored_custom_end = active_custom_dates()
default_custom_start = stored_custom_start or (today - pd.DateOffset(years=1)).date()
default_custom_end = stored_custom_end or today.date()

with filtros_sidebar:
    render_portfolio_scope_note()

    horizonte = st.selectbox(
        "Horizonte de análisis",
        HORIZON_OPTIONS,
        index=horizon_index(),
        key="signals_horizonte",
    )

    custom_start = None
    custom_end = None
    if horizonte == "Personalizado":
        c1, c2 = st.columns(2)
        with c1:
            custom_start = st.date_input(
                "Fecha inicial",
                value=default_custom_start,
                max_value=today.date(),
                key="signals_custom_start",
            )
        with c2:
            custom_end = st.date_input(
                "Fecha final",
                value=default_custom_end,
                max_value=today.date(),
                key="signals_custom_end",
            )

    rsi_overbought = st.slider("RSI sobrecompra", 50, 90, 70, 1, key="signals_rsi_overbought")
    rsi_oversold = st.slider("RSI sobreventa", 10, 50, 30, 1, key="signals_rsi_oversold")
    stoch_overbought = st.slider("Estocástico sobrecompra", 50, 95, 80, 1, key="signals_stoch_overbought")
    stoch_oversold = st.slider("Estocástico sobreventa", 5, 50, 20, 1, key="signals_stoch_oversold")
    sma_short_window = st.slider("SMA corta", 5, 80, 20, 1, key="signals_sma_short_window")
    sma_long_min = max(int(sma_short_window) + 1, 20)
    sma_long_window = st.slider("SMA larga", sma_long_min, 260, max(50, sma_long_min), 1, key="signals_sma_long_window")

start_date, end_date = _resolve_dates(
    horizonte=horizonte,
    default_end=today,
    custom_start=pd.Timestamp(custom_start) if custom_start is not None else None,
    custom_end=pd.Timestamp(custom_end) if custom_end is not None else None,
)

if start_date >= end_date:
    st.error("La fecha inicial debe ser menor que la fecha final.")
    st.stop()

_inject_signal_styles()

header_dashboard(
    "Mód. 7: Señales técnicas",
    "Convierte indicadores técnicos en alertas de compra, venta o neutralidad por activo.",
    modo=modo,
)

if modo == "General":
    nota(
        "Este módulo resume señales técnicas en un formato tipo semáforo. "
        "Cada alerta se deriva de indicadores como RSI, MACD, Bollinger, medias móviles y Estocástico."
    )
else:
    nota(
        "En modo estadístico se enfatiza la lógica de activación de señales, los umbrales configurables "
        "y la comparación de señales alcistas, bajistas y neutrales entre activos."
    )

asset_results: list[dict] = []
errors: list[str] = []

for asset in portfolio_assets:
    payload, err = _fetch_alerts_for_asset(
        ticker=asset["ticker"],
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        rsi_overbought=float(rsi_overbought),
        rsi_oversold=float(rsi_oversold),
        stoch_overbought=float(stoch_overbought),
        stoch_oversold=float(stoch_oversold),
        sma_short_window=int(sma_short_window),
        sma_long_window=int(sma_long_window),
    )

    if err:
        errors.append(f"{asset['ticker']}: {err}")
        asset_results.append({"ticker": asset["ticker"], "name": asset["name"], "alerts": []})
        continue

    alerts = _extract_alert_items(payload)
    asset_results.append({"ticker": asset["ticker"], "name": asset["name"], "alerts": alerts})

render_meta_row(
    [
        ("Horizonte", horizonte),
        ("RSI", f"{rsi_oversold}/{rsi_overbought}"),
        ("SMA corta/larga", f"{sma_short_window}/{sma_long_window}"),
        ("Estocástico", f"{stoch_oversold}/{stoch_overbought}"),
        ("Activos", str(len(portfolio_assets))),
    ]
)

if errors:
    st.warning("Algunas consultas de señales no devolvieron datos completos.")
    with st.expander("Ver detalle de errores", expanded=False):
        for err in errors:
            st.write(f"- {err}")

summary_df = _build_summary_rows(asset_results)

seccion("Resumen del módulo")

k1, k2, k3, k4 = st.columns(4)
with k1:
    tarjeta_kpi("Activos monitoreados", str(len(asset_results)), subtexto="Universo revisado por el motor de alertas.")
with k2:
    tarjeta_kpi("Señales de compra", str(int(summary_df["Compra"].sum())) if not summary_df.empty else "0", subtexto="Alertas alcistas detectadas.")
with k3:
    tarjeta_kpi("Señales de venta", str(int(summary_df["Venta"].sum())) if not summary_df.empty else "0", subtexto="Alertas bajistas detectadas.")
with k4:
    tarjeta_kpi("Neutrales", str(int(summary_df["Neutral"].sum())) if not summary_df.empty else "0", subtexto="Lecturas sin activación operativa.")

render_info_card(
    "Lectura general",
    (
        "El motor de señales no predice el precio futuro de forma automática. "
        "Su función es resumir condiciones técnicas observadas: momentum, sobrecompra, sobreventa, cruces de tendencia "
        "y ruptura de bandas. Por eso, una señal de compra o venta debe interpretarse como apoyo al análisis, "
        "no como una recomendación absoluta de inversión."
    ),
)

seccion("Panel de alertas por activo")

for item in asset_results:
    alerts = item.get("alerts", [])
    _render_asset_signal_header(item)

    if not alerts:
        render_info_card(
            "Sin alertas activas",
            (
                "No se activaron señales técnicas claras para este activo en el horizonte seleccionado. "
                "Esto no significa error: indica que los indicadores no cruzaron los umbrales definidos para compra o venta."
            ),
        )
        continue

    rows = [alerts[i:i + 2] for i in range(0, len(alerts), 2)]
    for row in rows:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            _render_signal_card(row[0])
        if len(row) > 1:
            with c2:
                _render_signal_card(row[1])
        else:
            with c2:
                st.empty()

    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)

seccion("Síntesis comparativa")

plot_card_header(
    "Resumen por activo",
    "Conteo rápido de señales de compra, venta y neutralidad técnica.",
    modo=modo,
    caption="Útil para sustentar qué activo concentra más activaciones y cuál permanece estable.",
)
st.dataframe(summary_df, use_container_width=True, hide_index=True)

plot_card_footer(
    "Una lectura neutral no es un error del modelo. Significa que, bajo los umbrales configurados, "
    "el indicador no activó una condición suficientemente clara de compra o venta."
)
