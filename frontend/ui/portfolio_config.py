from __future__ import annotations

import random
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.asset_metadata import display_country
from ui.benchmarking import resolve_benchmark
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_ui import nota, tarjeta_kpi
from ui.formatting import format_number, format_percent


PROFILE_TO_PERRI_OBJECTIVE = {
    "conservador": "min_risk",
    "moderado": "max_sharpe",
    "agresivo": "max_return",
}

OBJECTIVE_TO_PROFILE = {
    "min_risk": "conservador",
    "max_sharpe": "moderado",
    "max_return": "agresivo",
}

OBJECTIVE_LABELS = {
    "min_risk": "Conservador · mínimo riesgo",
    "max_sharpe": "Moderado · mejor Sharpe",
    "max_return": "Agresivo · máxima rentabilidad",
}

PROFILE_LABELS = {
    "conservador": "Conservador",
    "moderado": "Moderado",
    "agresivo": "Agresivo",
}

HORIZON_LABELS = {
    "1y": "1 año",
    "2y": "2 años",
    "3y": "3 años",
    "5y": "5 años",
    "custom": "Fechas personalizadas",
}

PERRI_HORIZON_LABELS = {
    "1y": "1 año",
    "3y": "3 años",
    "5y": "5 años",
}

BENCHMARK_OPTIONS = {
    "auto": "Automático según composición",
    "SPY": "S&P 500 - SPY",
    "ACWI": "MSCI ACWI global - ACWI",
}


def _format_pct(value: Any) -> str:
    return format_percent(value)


def _format_num(value: Any) -> str:
    return format_number(value)


def _weight_key(ticker: str, index: int) -> str:
    return f"global_weight_{ticker}_{index}"


def _normalize_weights(weights: list[float], target: float = 100.0) -> list[float]:
    if not weights:
        return []

    rounded = [round(max(float(value), 0.0), 4) for value in weights]
    residual = round(target - sum(rounded), 4)
    rounded[-1] = round(max(rounded[-1] + residual, 0.0), 4)
    return rounded


def _random_weights(count: int) -> list[float]:
    if count <= 0:
        return []

    raw = [random.random() for _ in range(count)]
    total = sum(raw) or 1.0
    weights = [(value / total) * 100.0 for value in raw]
    return _normalize_weights(weights)


def _asset_label(asset: dict[str, Any]) -> str:
    name = asset.get("name", "Activo")
    ticker = asset.get("ticker", "")
    country = display_country(asset)
    asset_type = _asset_type_label(asset)
    benchmark = resolve_benchmark([asset])["ticker"]
    return f"{asset_type['short']} · {name} · {ticker} · País: {country} · BM: {benchmark}"


def _selected_assets_table(assets: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for asset in assets:
        asset_type = _asset_type_label(asset)
        rows.append(
            {
                "Clase": asset_type["short"],
                "Activo": asset.get("name", "N/D"),
                "Ticker": asset.get("ticker", "N/D"),
                "País": display_country(asset),
                "BM": resolve_benchmark([asset])["ticker"],
            }
        )
    return pd.DataFrame(rows)


def _asset_type_key(asset: dict[str, Any]) -> str:
    raw_type = (
        asset.get("asset_type")
        or asset.get("tipo_activo")
        or asset.get("type")
        or asset.get("category")
        or ""
    )
    normalized = str(raw_type).strip().lower()

    if normalized in {"renta_fija", "fixed_income", "bond", "bonds"}:
        return "renta_fija"
    if normalized in {"renta_variable", "equity", "stock", "stocks", "accion", "acciones"}:
        return "renta_variable"

    ticker = str(asset.get("ticker", "")).upper()
    name = str(asset.get("name", "")).lower()
    fixed_income_tokens = {"AGG", "BND", "SHY", "IEF", "TLT", "LQD", "HYG", "MUB", "TIP"}
    if ticker in fixed_income_tokens or any(token in name for token in ["bond", "treasury", "bono", "deuda"]):
        return "renta_fija"

    return "renta_variable"


def _asset_type_label(asset: dict[str, Any]) -> dict[str, str]:
    if _asset_type_key(asset) == "renta_fija":
        return {"short": "RF", "label": "Renta fija"}
    return {"short": "RV", "label": "Renta variable"}


def _country_key(asset: dict[str, Any]) -> str:
    country = display_country(asset).strip().upper()
    if country.startswith("ESTADOS UNIDOS"):
        return "US"
    if country.startswith("GLOBAL"):
        return "GLOBAL"
    if country.startswith("MERCADOS EMERGENTES"):
        return "EM"
    if country.startswith("MERCADOS DESARROLLADOS"):
        return "DM"
    aliases = {
        "UNITED STATES": "US",
        "USA": "US",
        "ESTADOS UNIDOS": "US",
        "UNITED KINGDOM": "UK",
        "GB": "UK",
        "JAPAN": "JP",
        "CANADA": "CA",
        "MEXICO": "MX",
        "FRANCE": "FR",
        "COLOMBIA": "CO",
    }
    return aliases.get(country, country or "N/D")


def _benchmark_from_assets(assets: list[dict[str, Any]]) -> dict[str, str]:
    return resolve_benchmark(assets)


def _manual_benchmark_choice(ticker: str) -> dict[str, str]:
    ticker = str(ticker or "ACWI").strip().upper()
    if ticker == "SPY":
        return {
            "ticker": "SPY",
            "name": "S&P 500 ETF",
            "criterion": "manual_sp500",
            "reason": "Seleccionado manualmente para comparar contra acciones que cotizan en el S&P 500.",
            "explanation": "SPY se usa como proxy descargable del S&P 500.",
        }

    return {
        "ticker": "ACWI",
        "name": "MSCI ACWI ETF",
        "criterion": "manual_global",
        "reason": "Seleccionado manualmente como benchmark global para portafolios internacionales o mixtos.",
        "explanation": "ACWI se usa como referencia global para portafolios con renta variable, renta fija o exposición a distintos índices bursátiles.",
    }


def _fallback_assets() -> list[dict[str, Any]]:
    return [
        {"name": "Seven & i Holdings", "ticker": "3382.T", "country": "JP", "default": True},
        {"name": "Alimentation Couche-Tard", "ticker": "ATD.TO", "country": "CA", "default": True},
        {"name": "FEMSA", "ticker": "FEMSAUBD.MX", "country": "MX", "default": True},
        {"name": "BP", "ticker": "BP.L", "country": "UK", "default": True},
        {"name": "Carrefour", "ticker": "CA.PA", "country": "FR", "default": True},
    ]


def _load_assets() -> tuple[list[dict[str, Any]], int, str | None]:
    client = get_api_client()

    try:
        payload = client.get_assets()
        assets = payload.get("assets", [])
        max_allowed = int(payload.get("max_assets_allowed", 15))
        if not assets:
            return _fallback_assets(), 15, "La API no devolvió activos; se usó portafolio base."
        return assets, max_allowed, None
    except Exception as exc:
        return _fallback_assets(), 15, f"No fue posible cargar activos desde backend: {exc}"


def _asset_from_ticker(ticker: str, assets_by_ticker: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ticker = ticker.strip().upper()
    if ticker in assets_by_ticker:
        return assets_by_ticker[ticker]

    return {
        "name": ticker,
        "ticker": ticker,
        "country": "N/D",
        "default": False,
    }


def _get_effective_kyc_profile() -> tuple[str, dict[str, Any]]:
    user_kyc = st.session_state.get("user_kyc_data", {}) or {}

    fallback_profile = str(user_kyc.get("fallback_profile", "moderado")).lower()
    if fallback_profile not in PROFILE_LABELS:
        fallback_profile = "moderado"

    payload = {
        "age": int(user_kyc.get("age", 30)),
        "experience": int(user_kyc.get("experience", 2)),
        "tolerance": int(user_kyc.get("tolerance", 3)),
    }

    client = get_api_client()

    try:
        result = client.suggest_kyc_profile(payload)
        profile = str(result.get("suggested_profile", fallback_profile)).lower()
        if profile not in PROFILE_LABELS:
            profile = fallback_profile

        st.session_state["kyc_profile"] = profile
        st.session_state["kyc_score"] = result.get("score")
        st.session_state["kyc_explanation"] = result.get("explanation")

        return profile, {
            **payload,
            "suggested_profile": profile,
            "score": result.get("score"),
            "explanation": result.get("explanation"),
            "source": "backend_kyc",
        }
    except Exception:
        st.session_state["kyc_profile"] = fallback_profile
        return fallback_profile, {
            **payload,
            "suggested_profile": fallback_profile,
            "score": None,
            "explanation": "Se usó el perfil base del usuario porque KYC no respondió.",
            "source": "login_fallback",
        }


def _reference_horizon_for_perri(horizon_type: str) -> str:
    if horizon_type in {"1y", "3y", "5y"}:
        return horizon_type
    if horizon_type == "2y":
        return "3y"
    return "5y"


def _preferred_size_for_profile(profile: str) -> int:
    if profile == "conservador":
        return 5
    if profile == "agresivo":
        return 15
    return 10


def _perri_result(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload.get("result", payload)
    return result if isinstance(result, dict) else {}


def _build_perri_options(perri_payload: dict[str, Any]) -> list[dict[str, Any]]:
    result = _perri_result(perri_payload)
    horizons = result.get("horizons", {})

    options: list[dict[str, Any]] = []

    for horizon in ["1y", "3y", "5y"]:
        horizon_payload = horizons.get(horizon, {})
        sizes_payload = horizon_payload.get("portfolio_sizes", {})

        for size in [5, 10, 15]:
            size_payload = sizes_payload.get(str(size), {})

            for objective in ["min_risk", "max_sharpe", "max_return"]:
                portfolio = size_payload.get(objective)

                if not isinstance(portfolio, dict):
                    continue

                risk_profile = OBJECTIVE_TO_PROFILE.get(objective, "moderado")
                label = (
                    f"{OBJECTIVE_LABELS[objective]} · "
                    f"{size} activos · {PERRI_HORIZON_LABELS[horizon]}"
                )

                options.append(
                    {
                        "label": label,
                        "horizon": horizon,
                        "size": size,
                        "objective": objective,
                        "risk_profile": risk_profile,
                        "portfolio": portfolio,
                    }
                )

    return options


def _find_user_recommended_option(
    options: list[dict[str, Any]],
    profile: str,
    preferred_horizon: str,
) -> dict[str, Any] | None:
    objective = PROFILE_TO_PERRI_OBJECTIVE.get(profile, "max_sharpe")
    horizon = _reference_horizon_for_perri(preferred_horizon)
    size = _preferred_size_for_profile(profile)

    for option in options:
        if (
            option["objective"] == objective
            and option["horizon"] == horizon
            and option["size"] == size
        ):
            return option

    for option in options:
        if option["objective"] == objective and option["size"] == size:
            return option

    for option in options:
        if option["objective"] == objective:
            return option

    return options[0] if options else None


def _weights_pct_from_perri(portfolio: dict[str, Any]) -> list[float]:
    weights = portfolio.get("weights", [])
    if not isinstance(weights, list):
        return []

    return [round(float(item.get("weight", 0.0)) * 100.0, 8) for item in weights]


def _tickers_from_perri(portfolio: dict[str, Any]) -> list[str]:
    weights = portfolio.get("weights", [])
    if not isinstance(weights, list):
        return []

    return [
        str(item.get("asset", "")).strip().upper()
        for item in weights
        if str(item.get("asset", "")).strip()
    ]


def _perri_reference_payload(option: dict[str, Any]) -> dict[str, Any]:
    portfolio = option["portfolio"]

    return {
        "available": True,
        "source": "perri_precalculated",
        "horizon": option["horizon"],
        "size": option["size"],
        "objective": option["objective"],
        "risk_profile": option["risk_profile"],
        "expected_return_annual": portfolio.get("expected_return_annual"),
        "volatility_annual": portfolio.get("volatility_annual"),
        "sharpe": portfolio.get("sharpe"),
        "beta": portfolio.get("beta"),
        "alpha_annual": portfolio.get("alpha_annual"),
        "weights": portfolio.get("weights", []),
        "message": (
            f"Portafolio precalculado: {OBJECTIVE_LABELS.get(option['objective'])}, "
            f"{option['size']} activos, horizonte {option['horizon']}."
        ),
    }


def _validate_and_store_config(
    *,
    tickers: list[str],
    weights_pct: list[float],
    assets: list[dict[str, Any]],
    horizon_type: str,
    risk_profile: str,
    kyc_payload: dict[str, Any],
    perri_reference: dict[str, Any],
    benchmark: dict[str, str] | None = None,
    confidence_level: float = 0.95,
    custom_start: date | None = None,
    custom_end: date | None = None,
) -> tuple[bool, str | None]:
    client = get_api_client()
    normalized_confidence = float(confidence_level)

    preferences_payload = {
        "tickers": tickers,
        "weights_pct": weights_pct,
        "base_currency": "USD",
        "confidence_level": normalized_confidence,
        "risk_profile": risk_profile,
        "horizon_type": horizon_type,
        "return_type": "log",
        "mode": "general",
    }

    if horizon_type == "custom":
        preferences_payload["start"] = custom_start.isoformat() if custom_start else None
        preferences_payload["end"] = custom_end.isoformat() if custom_end else None

    try:
        validated = client.validate_investor_preferences(preferences_payload)
    except ApiClientError as exc:
        return False, f"El backend rechazó la configuración: {exc.message}"
    except Exception as exc:
        return False, f"Error inesperado validando la configuración: {exc}"

    global_config = {
        **validated,
        "assets": assets,
        "kyc": kyc_payload,
        "perri_reference": perri_reference,
        "benchmark": benchmark or _benchmark_from_assets(assets),
    }

    st.session_state["portfolio_config"] = global_config
    st.session_state["robo_portfolio"] = assets
    st.session_state["kyc_profile"] = risk_profile
    st.session_state["confidence_level"] = normalized_confidence
    st.session_state["var_confidence_level"] = normalized_confidence
    st.session_state.pop("portfolio_persistence_warning", None)

    try:
        client.save_portfolio(
            {
                "name": f"Portafolio {risk_profile} - {horizon_type}",
                "owner": st.session_state.get("user_name") or "streamlit_user",
                "description": "Configuracion creada desde el modulo Inicio.",
                "tickers": tickers,
                "weights_pct": weights_pct,
                "horizon": horizon_type,
                "benchmark": global_config["benchmark"],
                "base_currency": global_config.get("base_currency", "USD"),
                "confidence_level": normalized_confidence,
            }
        )
    except Exception as exc:
        st.session_state["portfolio_persistence_warning"] = (
            f"La configuracion quedo activa en la sesion, pero no se pudo persistir en backend: {exc}"
        )

    return True, None


def _apply_perri_option(
    option: dict[str, Any],
    assets_by_ticker: dict[str, dict[str, Any]],
    kyc_payload: dict[str, Any],
) -> None:
    portfolio = option["portfolio"]
    tickers = _tickers_from_perri(portfolio)
    weights_pct = _weights_pct_from_perri(portfolio)
    assets = [_asset_from_ticker(ticker, assets_by_ticker) for ticker in tickers]

    ok, error = _validate_and_store_config(
        tickers=tickers,
        weights_pct=weights_pct,
        assets=assets,
        horizon_type=option["horizon"],
        risk_profile=option["risk_profile"],
        kyc_payload=kyc_payload,
        perri_reference=_perri_reference_payload(option),
        benchmark=_benchmark_from_assets(assets),
        confidence_level=0.95,
    )

    if not ok:
        st.error(error)
        return

    st.success("Portafolio aplicado como configuración global.")
    if st.session_state.get("portfolio_persistence_warning"):
        st.warning(st.session_state["portfolio_persistence_warning"])
    st.switch_page("pages/0_Contextualizacion.py")


def _current_config_summary() -> None:
    config = st.session_state.get("portfolio_config")
    if not config:
        render_info_card(
            "Configuración pendiente",
            "Puedes usar la recomendación automática, elegir un portafolio precalculado o crear tu propio portafolio manual.",
        )
        return

    tickers = config.get("tickers", [])
    perri = config.get("perri_reference", {})
    benchmark = config.get("benchmark", {}) or {}

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        tarjeta_kpi("Activos", str(len(tickers)), subtexto="Máximo 15")
    with c2:
        tarjeta_kpi(
            "Horizonte",
            HORIZON_LABELS.get(config.get("horizon_type"), config.get("horizon_type", "N/D")),
            subtexto=f"{config.get('start')} a {config.get('end')}",
        )
    with c3:
        tarjeta_kpi("Perfil", str(config.get("risk_profile", "N/D")).upper(), subtexto="KYC / selección")
    with c4:
        tarjeta_kpi("Moneda", config.get("base_currency", "USD"), subtexto="Base metodológica")
    with c5:
        tarjeta_kpi("Benchmark", benchmark.get("ticker", "N/D"), subtexto=benchmark.get("name", "Referencia"))

    render_meta_row(
        {
            "Tickers": ", ".join(tickers),
            "Pesos": ", ".join(f"{w:.2f}%" for w in config.get("weights_pct", [])),
            "Origen": perri.get("source", "manual"),
            "Benchmark": benchmark.get("ticker", "N/D"),
        }
    )


def _render_portfolio_config_styles() -> None:
    st.markdown(
        """
        <style>
            .portfolio-date-panel {
                border: 1px solid rgba(148, 163, 184, 0.28);
                border-radius: 14px;
                background: rgba(15, 23, 42, 0.48);
                padding: 0.85rem 1rem 0.35rem 1rem;
                margin: 0.75rem 0 0.95rem 0;
            }

            .portfolio-date-panel-title {
                color: #E2E8F0;
                font-size: 0.92rem;
                font-weight: 850;
                margin-bottom: 0.15rem;
            }

            .portfolio-date-panel-caption {
                color: #94A3B8;
                font-size: 0.80rem;
                margin-bottom: 0.65rem;
            }

            .portfolio-highlight-control {
                border: 1px solid rgba(56, 189, 248, 0.30);
                border-radius: 14px;
                background: rgba(14, 116, 144, 0.13);
                padding: 0.85rem 1rem 1rem 1rem;
                margin: 0.45rem 0 0.85rem 0;
            }

            .stTabs [data-baseweb="tab-list"] {
                gap: 0.7rem !important;
                width: 100% !important;
                background: linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(17, 24, 39, 0.86)) !important;
                border: 1px solid rgba(56, 189, 248, 0.26) !important;
                border-radius: 18px !important;
                padding: 0.5rem !important;
                box-shadow: 0 16px 34px rgba(2, 8, 23, 0.24) !important;
            }

            .stTabs [data-baseweb="tab"] {
                min-height: 54px !important;
                padding: 0.7rem 1.05rem !important;
                border-radius: 14px !important;
                background: rgba(30, 41, 59, 0.72) !important;
                color: #DDE7F5 !important;
                border: 1px solid rgba(148, 163, 184, 0.22) !important;
                font-weight: 900 !important;
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
            }

            .stTabs [data-baseweb="tab"]:hover {
                background: rgba(30, 64, 175, 0.34) !important;
                border-color: rgba(56, 189, 248, 0.42) !important;
                color: #FFFFFF !important;
            }

            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #38BDF8 0%, #2563EB 100%) !important;
                color: #FFFFFF !important;
                border-color: rgba(125, 211, 252, 0.78) !important;
                box-shadow: 0 12px 24px rgba(37, 99, 235, 0.30) !important;
            }

            .portfolio-manual-title {
                color: #F8FAFC;
                font-size: 1.08rem;
                font-weight: 900;
                margin: 0 0 0.25rem 0;
            }

            .portfolio-manual-caption {
                color: #AAB6C5;
                font-size: 0.86rem;
                margin: 0 0 0.9rem 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_perri_portfolio_card(
    option: dict[str, Any],
    title: str,
    assets_by_ticker: dict[str, dict[str, Any]],
) -> None:
    portfolio = option["portfolio"]
    weights = portfolio.get("weights", [])

    st.markdown(f"#### {title}")
    st.caption(option["label"])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta_kpi("Retorno", _format_pct(portfolio.get("expected_return_annual")), subtexto="Esperado anual")
    with c2:
        tarjeta_kpi("Volatilidad", _format_pct(portfolio.get("volatility_annual")), subtexto="Anual")
    with c3:
        tarjeta_kpi("Sharpe", _format_num(portfolio.get("sharpe")), subtexto="Riesgo-retorno")
    with c4:
        tarjeta_kpi("Perfil", PROFILE_LABELS.get(option["risk_profile"], "N/D"), subtexto=f"{option['size']} activos")

    if isinstance(weights, list) and weights:
        df = pd.DataFrame(weights)
        if not df.empty and {"asset", "weight"}.issubset(df.columns):
            df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
            df["Activo"] = df["asset"].apply(
                lambda ticker: _asset_label(_asset_from_ticker(str(ticker), assets_by_ticker))
            )
            df["Peso"] = df["weight"].apply(lambda value: f"{float(value):.2%}")
            df = df[["Activo", "Peso"]]
            st.dataframe(df, use_container_width=True, hide_index=True)


def render_global_portfolio_config() -> None:
    _render_portfolio_config_styles()

    assets, max_allowed, load_warning = _load_assets()
    assets_by_ticker = {
        str(asset.get("ticker", "")).strip().upper(): asset
        for asset in assets
        if str(asset.get("ticker", "")).strip()
    }

    if load_warning:
        st.warning(load_warning)

    profile, kyc_payload = _get_effective_kyc_profile()
    preferred_horizon = st.session_state.get("user_preferred_horizon", "3y")

    client = get_api_client()
    try:
        perri_payload = client.get_perri_latest()
        perri_options = _build_perri_options(perri_payload)
    except Exception as exc:
        perri_options = []
        st.warning(f"No fue posible cargar portafolios precalculados: {exc}")

    recommended_option = _find_user_recommended_option(
        options=perri_options,
        profile=profile,
        preferred_horizon=preferred_horizon,
    )

    st.markdown("### Configuración inicial global del portafolio")

    _current_config_summary()

    st.markdown("---")

    tab_manual, tab_auto, tab_perri = st.tabs(
        [
            "Crear mi portafolio",
            "Recomendado para mí",
            "Portafolios precalculados",
        ]
    )

    with tab_auto:
        render_meta_row(
            {
                "Usuario": st.session_state.get("user_name", "N/D"),
                "Perfil KYC": PROFILE_LABELS.get(profile, profile),
                "Edad": kyc_payload.get("age"),
                "Experiencia": f"{kyc_payload.get('experience')} años",
                "Tolerancia": f"{kyc_payload.get('tolerance')}/5",
                "Horizonte sugerido": HORIZON_LABELS.get(preferred_horizon, preferred_horizon),
            }
        )

        if recommended_option:
            _render_perri_portfolio_card(
                recommended_option,
                "Portafolio recomendado automáticamente",
                assets_by_ticker,
            )

            if st.button(
                "Usar este portafolio recomendado",
                type="primary",
                use_container_width=True,
                key="apply_auto_perri_portfolio",
            ):
                _apply_perri_option(recommended_option, assets_by_ticker, kyc_payload)
        else:
            render_info_card(
                "Recomendación no disponible",
                "No se encontró un portafolio precalculado compatible para el perfil actual.",
            )

    with tab_perri:
        if not perri_options:
            render_info_card(
                "Sin portafolios precalculados",
                "No fue posible cargar el JSON de portafolios precalculados desde el backend.",
            )
        else:
            labels = [option["label"] for option in perri_options]
            with st.container(border=True):
                st.markdown("#### Elige un portafolio precalculado")
                selected_label = st.selectbox(
                    "Portafolio",
                    options=labels,
                    index=0,
                    label_visibility="collapsed",
                    help="Estos portafolios vienen del JSON precalculado por la acción de GitHub.",
                )

            selected_option = perri_options[labels.index(selected_label)]
            _render_perri_portfolio_card(
                selected_option,
                "Detalle del portafolio seleccionado",
                assets_by_ticker,
            )

            if st.button(
                "Usar este portafolio precalculado",
                type="primary",
                use_container_width=True,
                key="apply_selected_perri_portfolio",
            ):
                _apply_perri_option(selected_option, assets_by_ticker, kyc_payload)

    with tab_manual:
        label_to_asset = {_asset_label(asset): asset for asset in assets}
        ticker_to_label = {asset.get("ticker"): _asset_label(asset) for asset in assets}

        saved_config = st.session_state.get("portfolio_config", {})
        saved_tickers = saved_config.get("tickers", [])

        if saved_tickers:
            default_labels = [
                ticker_to_label[ticker]
                for ticker in saved_tickers
                if ticker in ticker_to_label
            ]
        else:
            default_labels = []

        with st.container(border=True):
            st.markdown(
                """
                <div class="portfolio-manual-title">Crear portafolio manual</div>
                <div class="portfolio-manual-caption">
                    Edita los activos, horizonte, confianza y pesos que se usarán para generar tu portafolio.
                </div>
                """,
                unsafe_allow_html=True,
            )

            selected_labels = st.multiselect(
                "Acciones / tickers del portafolio",
                options=list(label_to_asset.keys()),
                default=default_labels[:max_allowed],
                help=f"Selecciona entre 5 y {max_allowed} activos. RV = renta variable, RF = renta fija.",
            )

            selected_assets = [label_to_asset[label] for label in selected_labels]
            selected_tickers = [str(asset.get("ticker", "")).upper() for asset in selected_assets]
            selected_count = len(selected_tickers)
            manual_benchmark = _benchmark_from_assets(selected_assets)

            if selected_assets:
                st.dataframe(
                    _selected_assets_table(selected_assets),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Clase": st.column_config.TextColumn("RV/RF", width="small"),
                        "Activo": st.column_config.TextColumn("Nombre", width="large"),
                        "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                        "País": st.column_config.TextColumn("País", width="small"),
                        "BM": st.column_config.TextColumn("BM", width="small"),
                    },
                )

            c1, c2, c3 = st.columns(3)

            with c1:
                horizon_keys = list(HORIZON_LABELS.keys())
                saved_horizon = saved_config.get("horizon_type")
                default_horizon_index = (
                    horizon_keys.index(saved_horizon)
                    if saved_horizon in HORIZON_LABELS and saved_tickers
                    else None
                )
                horizon_type = st.selectbox(
                    "Horizonte de análisis",
                    options=horizon_keys,
                    format_func=lambda value: HORIZON_LABELS[value],
                    index=default_horizon_index,
                    placeholder="Selecciona un horizonte",
                    help="Debes elegir el horizonte antes de guardar el portafolio.",
                )

            with c2:
                st.text_input(
                    "Moneda base",
                    value="USD",
                    disabled=True,
                    help="Aunque el activo esté en otra moneda, el análisis se trabaja en dólares.",
                )

            with c3:
                confidence_level = st.selectbox(
                    "Nivel de confianza VaR",
                    options=[0.95, 0.975, 0.99],
                    index=0,
                    format_func=lambda value: f"{value:.1%}",
                    help="Se usa 95% por defecto para que el VaR/CVaR tenga una referencia estándar desde el inicio.",
                )

            benchmark_choice_keys = list(BENCHMARK_OPTIONS.keys())
            default_benchmark_choice = "auto"

            benchmark_choice = st.selectbox(
                "Benchmark del portafolio",
                options=benchmark_choice_keys,
                index=benchmark_choice_keys.index(default_benchmark_choice),
                format_func=lambda value: BENCHMARK_OPTIONS[value],
                help=(
                    "Automático usa SPY cuando todos los activos son renta variable de Estados Unidos; "
                    "usa ACWI cuando el portafolio es internacional, mixto o combina renta variable y renta fija."
                ),
            )

            selected_benchmark = (
                manual_benchmark
                if benchmark_choice == "auto"
                else _manual_benchmark_choice(benchmark_choice)
            )

            st.info(
                "Benchmark seleccionado: "
                f"{selected_benchmark['ticker']} ({selected_benchmark['name']}). "
                f"{selected_benchmark['reason']}"
            )

            custom_start = None
            custom_end = None
            if horizon_type == "custom":
                st.markdown(
                    """
                    <div class="portfolio-date-panel">
                        <div class="portfolio-date-panel-title">Rango personalizado</div>
                        <div class="portfolio-date-panel-caption">Define las fechas exactas para calcular el portafolio.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                with st.container(border=True):
                    d1, d2 = st.columns(2)
                    with d1:
                        custom_start = st.date_input(
                            "Fecha inicial",
                            value=date(date.today().year - 1, date.today().month, date.today().day),
                            max_value=date.today(),
                        )
                    with d2:
                        custom_end = st.date_input(
                            "Fecha final",
                            value=date.today(),
                            max_value=date.today(),
                        )

            st.markdown("#### Perfil KYC aplicado al portafolio manual")
            render_meta_row(
                {
                    "Perfil": PROFILE_LABELS.get(profile, profile),
                    "Edad": kyc_payload.get("age"),
                    "Experiencia": f"{kyc_payload.get('experience')} años",
                    "Tolerancia": f"{kyc_payload.get('tolerance')}/5",
                }
            )

            random_col, equal_col, hint_col = st.columns([0.30, 0.30, 0.40])
            with random_col:
                randomize_weights = st.button(
                    "Asignar pesos aleatorios",
                    use_container_width=True,
                    disabled=selected_count == 0,
                    key="manual_random_weights",
                )
            with equal_col:
                equalize_weights = st.button(
                    "Asignar pesos iguales",
                    use_container_width=True,
                    disabled=selected_count == 0,
                    key="manual_equal_weights",
                )
            with hint_col:
                st.caption("Si la suma queda casi en 100%, el sistema ajusta el último decimal al guardar.")

            if randomize_weights:
                generated_weights = _random_weights(selected_count)
                for idx, ticker in enumerate(selected_tickers):
                    st.session_state[_weight_key(ticker, idx)] = generated_weights[idx]
                st.rerun()

            if equalize_weights:
                generated_weights = _normalize_weights([100.0 / selected_count] * selected_count)
                for idx, ticker in enumerate(selected_tickers):
                    st.session_state[_weight_key(ticker, idx)] = generated_weights[idx]
                st.rerun()

            with st.form("global_portfolio_config_form"):
                st.markdown("#### Pesos / asignación inicial")

                if selected_count == 0:
                    st.warning("Selecciona mínimo 5 activos para crear tu portafolio manual.")
                    weights_pct = []
                else:
                    equal_weight = round(100.0 / selected_count, 4)
                    weights_pct = []
                    weight_cols = st.columns(min(selected_count, 5))

                    for idx, ticker in enumerate(selected_tickers):
                        with weight_cols[idx % min(selected_count, 5)]:
                            default_weight = equal_weight
                            if saved_config.get("tickers") == selected_tickers:
                                old_weights = saved_config.get("weights_pct", [])
                                if idx < len(old_weights):
                                    default_weight = float(old_weights[idx])

                            value = st.number_input(
                                ticker,
                                min_value=0.0,
                                max_value=100.0,
                                value=float(st.session_state.get(_weight_key(ticker, idx), default_weight)),
                                step=0.25,
                                format="%.4f",
                                key=_weight_key(ticker, idx),
                            )
                            weights_pct.append(float(value))

                total_weight = sum(weights_pct)
                st.caption(f"Total asignado: {total_weight:.4f}%")

                submitted = st.form_submit_button(
                    "Guardar mi portafolio manual",
                    type="primary",
                    use_container_width=True,
                )

        if submitted:
            errors = []
            adjusted_weights_pct = list(weights_pct)
            total_weight = sum(adjusted_weights_pct)

            if selected_count > 0 and 0 < abs(total_weight - 100.0) <= 0.10:
                adjusted_weights_pct = _normalize_weights(adjusted_weights_pct)
                total_weight = sum(adjusted_weights_pct)

            if selected_count < 5:
                errors.append("Debes seleccionar mínimo 5 activos para guardar tu portafolio manual.")
            if selected_count > max_allowed:
                errors.append(f"Solo se permiten máximo {max_allowed} activos.")
            if horizon_type is None:
                errors.append("Debes seleccionar un horizonte de análisis.")
            if confidence_level is None:
                errors.append("Debes seleccionar el nivel de confianza VaR.")
            if horizon_type == "custom" and custom_start and custom_end and custom_start >= custom_end:
                errors.append("La fecha inicial debe ser menor que la fecha final.")
            if abs(total_weight - 100.0) > 1e-6:
                errors.append("Los pesos deben sumar exactamente 100%.")

            if errors:
                for error in errors:
                    st.error(error)
                return

            manual_reference = {
                "available": False,
                "source": "manual",
                "risk_profile": profile,
                "benchmark": selected_benchmark,
                "message": "Portafolio creado manualmente por el usuario.",
            }

            ok, error = _validate_and_store_config(
                tickers=selected_tickers,
                weights_pct=adjusted_weights_pct,
                assets=selected_assets,
                horizon_type=horizon_type,
                risk_profile=profile,
                kyc_payload=kyc_payload,
                perri_reference=manual_reference,
                benchmark=selected_benchmark,
                confidence_level=float(confidence_level),
                custom_start=custom_start,
                custom_end=custom_end,
            )

            if not ok:
                st.error(error)
                return

            st.success("Portafolio manual guardado como configuración global.")
            if st.session_state.get("portfolio_persistence_warning"):
                st.warning(st.session_state["portfolio_persistence_warning"])
            st.switch_page("pages/0_Contextualizacion.py")

    config = st.session_state.get("portfolio_config")
    if config:
        source = config.get("perri_reference", {}).get("source", "manual")
        if source == "perri_precalculated":
            perri = config.get("perri_reference", {})
            nota(
                "Configuración activa desde portafolio precalculado: "
                f"retorno {_format_pct(perri.get('expected_return_annual'))}, "
                f"volatilidad {_format_pct(perri.get('volatility_annual'))}, "
                f"Sharpe {_format_num(perri.get('sharpe'))}."
            )
        else:
            nota("Configuración activa desde portafolio manual del usuario.")
