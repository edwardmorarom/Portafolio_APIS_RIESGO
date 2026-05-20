from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from services.api_client import ApiClientError, get_api_client
from ui.cards import render_info_card, render_meta_row
from ui.dashboard_ui import nota, tarjeta_kpi


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


def _format_pct(value: Any) -> str:
    try:
        return f"{float(value):.2%}"
    except Exception:
        return "N/D"


def _format_num(value: Any) -> str:
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "N/D"


def _asset_label(asset: dict[str, Any]) -> str:
    name = asset.get("name", "Activo")
    ticker = asset.get("ticker", "")
    country = asset.get("country", "")
    return f"{name} · {ticker} · {country}"


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
        "country": "Perri",
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
            f"Perri precalculado: {OBJECTIVE_LABELS.get(option['objective'])}, "
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
    confidence_level: float = 0.95,
    custom_start: date | None = None,
    custom_end: date | None = None,
) -> tuple[bool, str | None]:
    client = get_api_client()

    preferences_payload = {
        "tickers": tickers,
        "weights_pct": weights_pct,
        "base_currency": "USD",
        "confidence_level": float(confidence_level),
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
    }

    st.session_state["portfolio_config"] = global_config
    st.session_state["robo_portfolio"] = assets
    st.session_state["kyc_profile"] = risk_profile

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
        confidence_level=0.95,
    )

    if not ok:
        st.error(error)
        return

    st.success("Portafolio Perri aplicado como configuración global.")
    st.rerun()


def _current_config_summary() -> None:
    config = st.session_state.get("portfolio_config")
    if not config:
        render_info_card(
            "Configuración pendiente",
            "Puedes usar la recomendación automática, elegir un portafolio Perri precalculado o crear tu propio portafolio manual.",
        )
        return

    tickers = config.get("tickers", [])
    perri = config.get("perri_reference", {})

    c1, c2, c3, c4 = st.columns(4)
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

    render_meta_row(
        {
            "Tickers": ", ".join(tickers),
            "Pesos": ", ".join(f"{w:.2f}%" for w in config.get("weights_pct", [])),
            "Origen": perri.get("source", "manual"),
        }
    )


def _render_perri_portfolio_card(option: dict[str, Any], title: str) -> None:
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
            df["Peso"] = df["weight"].apply(lambda value: f"{float(value):.2%}")
            df = df[["asset", "Peso"]].rename(columns={"asset": "Activo"})
            st.dataframe(df, use_container_width=True, hide_index=True)


def render_global_portfolio_config() -> None:
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
        st.warning(f"No fue posible cargar portafolios Perri precalculados: {exc}")

    recommended_option = _find_user_recommended_option(
        options=perri_options,
        profile=profile,
        preferred_horizon=preferred_horizon,
    )

    st.markdown("### Configuración inicial global del portafolio")

    _current_config_summary()

    st.markdown("---")

    tab_auto, tab_perri, tab_manual = st.tabs(
        [
            "Recomendado para mí",
            "Portafolios Perri precalculados",
            "Crear mi portafolio",
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
                "No se encontró un portafolio Perri compatible para el perfil actual.",
            )

    with tab_perri:
        if not perri_options:
            render_info_card(
                "Sin portafolios precalculados",
                "No fue posible cargar backend/data/perri_latest_optimization.json desde el backend.",
            )
        else:
            labels = [option["label"] for option in perri_options]
            selected_label = st.selectbox(
                "Elige un portafolio precalculado",
                options=labels,
                index=0,
                help="Estos portafolios vienen del JSON precalculado por la acción de GitHub.",
            )

            selected_option = perri_options[labels.index(selected_label)]
            _render_perri_portfolio_card(
                selected_option,
                "Detalle del portafolio seleccionado",
            )

            if st.button(
                "Usar este portafolio Perri",
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
            default_labels = [
                _asset_label(asset)
                for asset in assets
                if bool(asset.get("default", False))
            ]

        if not default_labels:
            default_labels = list(label_to_asset.keys())[:5]

        with st.form("global_portfolio_config_form"):
            st.markdown("#### Crear portafolio manual")

            selected_labels = st.multiselect(
                "Acciones / tickers del portafolio",
                options=list(label_to_asset.keys()),
                default=default_labels[:max_allowed],
                help=f"Selecciona entre 1 y {max_allowed} activos.",
            )

            selected_assets = [label_to_asset[label] for label in selected_labels]
            selected_tickers = [str(asset.get("ticker", "")).upper() for asset in selected_assets]
            selected_count = len(selected_tickers)

            c1, c2, c3 = st.columns(3)

            with c1:
                horizon_keys = list(HORIZON_LABELS.keys())
                default_horizon = preferred_horizon if preferred_horizon in HORIZON_LABELS else "3y"
                horizon_type = st.selectbox(
                    "Horizonte de análisis",
                    options=horizon_keys,
                    format_func=lambda value: HORIZON_LABELS[value],
                    index=horizon_keys.index(default_horizon),
                    help="El usuario puede ajustar el horizonte antes de guardar.",
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
                )

            custom_start = None
            custom_end = None
            if horizon_type == "custom":
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

            st.markdown("#### Pesos / asignación inicial")

            if selected_count == 0:
                st.warning("Selecciona al menos un activo.")
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
                            value=float(default_weight),
                            step=1.0,
                            format="%.4f",
                            key=f"global_weight_{ticker}_{idx}",
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

            if selected_count < 1:
                errors.append("Debes seleccionar al menos un activo.")
            if selected_count > max_allowed:
                errors.append(f"Solo se permiten máximo {max_allowed} activos.")
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
                "message": "Portafolio creado manualmente por el usuario.",
            }

            ok, error = _validate_and_store_config(
                tickers=selected_tickers,
                weights_pct=weights_pct,
                assets=selected_assets,
                horizon_type=horizon_type,
                risk_profile=profile,
                kyc_payload=kyc_payload,
                perri_reference=manual_reference,
                confidence_level=float(confidence_level),
                custom_start=custom_start,
                custom_end=custom_end,
            )

            if not ok:
                st.error(error)
                return

            st.success("Portafolio manual guardado como configuración global.")
            st.rerun()

    config = st.session_state.get("portfolio_config")
    if config:
        source = config.get("perri_reference", {}).get("source", "manual")
        if source == "perri_precalculated":
            perri = config.get("perri_reference", {})
            nota(
                "Configuración activa desde Perri: "
                f"retorno {_format_pct(perri.get('expected_return_annual'))}, "
                f"volatilidad {_format_pct(perri.get('volatility_annual'))}, "
                f"Sharpe {_format_num(perri.get('sharpe'))}."
            )
        else:
            nota("Configuración activa desde portafolio manual del usuario.")
