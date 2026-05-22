from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from ui.asset_metadata import display_country
from ui.benchmarking import resolve_benchmark


HORIZON_OPTIONS = ["1 mes", "Trimestre", "Semestre", "1 año", "3 años", "5 años", "Personalizado"]

HORIZON_TYPE_TO_LABEL = {
    "1m": "1 mes",
    "3m": "Trimestre",
    "6m": "Semestre",
    "1y": "1 año",
    "2y": "1 año",
    "3y": "3 años",
    "5y": "5 años",
    "custom": "Personalizado",
}


def active_config() -> dict[str, Any]:
    return st.session_state.get("portfolio_config", {}) or {}


def active_tickers() -> list[str]:
    return [str(ticker).strip().upper() for ticker in active_config().get("tickers", []) if str(ticker).strip()]


def active_assets() -> list[dict[str, Any]]:
    assets = active_config().get("assets", []) or []
    return [asset for asset in assets if isinstance(asset, dict)]


def active_weights_pct() -> list[float]:
    values = active_config().get("weights_pct", []) or []
    return [float(value) for value in values]


def active_weights_decimal() -> list[float]:
    return [value / 100.0 for value in active_weights_pct()]


def active_benchmark_details(default: str = "ACWI") -> dict[str, str]:
    assets = active_assets()
    if assets:
        return resolve_benchmark(assets)

    benchmark = active_config().get("benchmark", {}) or {}
    if benchmark:
        return {
            "ticker": str(benchmark.get("ticker") or default).strip().upper(),
            "name": str(benchmark.get("name") or "Referencia"),
            "criterion": str(benchmark.get("criterion") or "stored"),
            "reason": str(benchmark.get("reason") or benchmark.get("explanation") or "Benchmark guardado en la configuración activa."),
            "explanation": str(benchmark.get("explanation") or benchmark.get("reason") or "Benchmark guardado en la configuración activa."),
        }

    return resolve_benchmark([])


def active_benchmark(default: str = "ACWI") -> str:
    details = active_benchmark_details(default=default)
    return str(details.get("ticker") or default).strip().upper()


def active_confidence_level(default: float = 0.95) -> float:
    value = active_config().get("confidence_level")
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return default
    if confidence > 1:
        confidence = confidence / 100.0
    return min(max(confidence, 0.0), 0.9999)


def active_horizon_label(default: str = "1 año") -> str:
    config = active_config()
    raw = str(config.get("horizon_type") or "").strip()
    return HORIZON_TYPE_TO_LABEL.get(raw, raw if raw in HORIZON_OPTIONS else default)


def horizon_index(default: str = "1 año") -> int:
    label = active_horizon_label(default=default)
    return HORIZON_OPTIONS.index(label) if label in HORIZON_OPTIONS else HORIZON_OPTIONS.index(default)


def active_custom_dates() -> tuple[date | None, date | None]:
    config = active_config()
    start = config.get("start")
    end = config.get("end")
    try:
        start_date = pd.Timestamp(start).date() if start else None
    except Exception:
        start_date = None
    try:
        end_date = pd.Timestamp(end).date() if end else None
    except Exception:
        end_date = None
    return start_date, end_date


def assets_for_active_portfolio(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tickers = active_tickers()
    if not tickers:
        return assets

    by_ticker = {
        str(asset.get("ticker", "")).strip().upper(): asset
        for asset in assets
        if str(asset.get("ticker", "")).strip()
    }

    return [by_ticker[ticker] for ticker in tickers if ticker in by_ticker]


def asset_label(asset: dict[str, Any]) -> str:
    name = asset.get("name", "Activo")
    ticker = asset.get("ticker", "N/D")
    country = display_country(asset)
    benchmark = resolve_benchmark([asset])["ticker"]
    return f"{name} · {ticker} · País: {country} · BM: {benchmark}"


def asset_options_for_active_portfolio(assets: list[dict[str, Any]]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    scoped_assets = assets_for_active_portfolio(assets)
    labels: list[str] = []
    asset_map: dict[str, dict[str, Any]] = {}

    for asset in scoped_assets:
        label = asset_label(asset)
        labels.append(label)
        asset_map[label] = asset

    return labels, asset_map


def weights_for_tickers(tickers: list[str]) -> tuple[list[float], float]:
    active = active_tickers()
    weights = active_weights_pct()
    by_ticker = {
        ticker: weights[index]
        for index, ticker in enumerate(active)
        if index < len(weights)
    }

    selected = [float(by_ticker.get(str(ticker).upper(), 0.0)) for ticker in tickers]
    total = sum(selected)
    if selected and abs(total - 100.0) > 1e-6 and total > 0:
        selected = [value * 100.0 / total for value in selected]
        total = sum(selected)
    return [value / 100.0 for value in selected], total


def render_portfolio_scope_note() -> None:
    tickers = active_tickers()
    if tickers:
        benchmark = active_benchmark()
        st.caption("Usando portafolio activo: " + ", ".join(tickers) + f" · Benchmark: {benchmark}")
