from __future__ import annotations

from typing import Any

import requests

from config import BACKEND_URL


TIMEOUT = 45


def _handle_response(response: requests.Response) -> Any:
    response.raise_for_status()
    return response.json()


def _get(path: str, params: dict | None = None) -> Any:
    response = requests.get(
        f"{BACKEND_URL}{path}",
        params=params,
        timeout=TIMEOUT,
    )
    return _handle_response(response)


def _post(path: str, payload: dict) -> Any:
    response = requests.post(
        f"{BACKEND_URL}{path}",
        json=payload,
        timeout=TIMEOUT,
    )
    return _handle_response(response)


# =========================
# Assets
# =========================
def get_assets() -> Any:
    return _get("/api/v1/assets/")


def search_assets(query: str) -> Any:
    return _get("/api/v1/assets/search", params={"query": query})


# =========================
# Help
# =========================
def get_help_catalog() -> Any:
    return _get("/api/v1/help/catalog")


# =========================
# Market
# =========================
def get_prices(ticker: str, start: str, end: str) -> Any:
    return _get(f"/api/v1/market/prices/{ticker}", params={"start": start, "end": end})


def get_returns(ticker: str, start: str, end: str) -> Any:
    return _get(f"/api/v1/market/returns/{ticker}", params={"start": start, "end": end})


# =========================
# Technical
# =========================
def get_technical_indicators(
    ticker: str,
    start: str,
    end: str,
    sma_window: int = 20,
    ema_window: int = 20,
    rsi_window: int = 14,
    bb_window: int = 20,
    stoch_window: int = 14,
) -> Any:
    return _get(
        f"/api/v1/technical/indicators/{ticker}",
        params={
            "start": start,
            "end": end,
            "sma_window": sma_window,
            "ema_window": ema_window,
            "rsi_window": rsi_window,
            "bb_window": bb_window,
            "stoch_window": stoch_window,
        },
    )


# =========================
# Returns stats
# =========================
def get_returns_stats_summary(
    ticker: str,
    start: str,
    end: str,
    return_type: str = "log",
    mode: str = "general",
) -> Any:
    return _get(
        f"/api/v1/returns-stats/summary/{ticker}",
        params={
            "start": start,
            "end": end,
            "return_type": return_type,
            "mode": mode,
        },
    )


# =========================
# Alerts
# =========================
def get_alerts(
    ticker: str,
    start: str,
    end: str,
    rsi_overbought: float = 70.0,
    rsi_oversold: float = 30.0,
    stoch_overbought: float = 80.0,
    stoch_oversold: float = 20.0,
) -> Any:
    return _get(
        f"/api/v1/alerts/{ticker}",
        params={
            "start": start,
            "end": end,
            "rsi_overbought": rsi_overbought,
            "rsi_oversold": rsi_oversold,
            "stoch_overbought": stoch_overbought,
            "stoch_oversold": stoch_oversold,
        },
    )


# =========================
# GARCH
# =========================
def get_garch(
    ticker: str,
    start: str,
    end: str,
    return_type: str = "log",
    mode: str = "general",
    forecast_horizon: int = 5,
) -> Any:
    return _get(
        f"/api/v1/garch/{ticker}",
        params={
            "start": start,
            "end": end,
            "return_type": return_type,
            "mode": mode,
            "forecast_horizon": forecast_horizon,
        },
    )


# =========================
# CAPM
# =========================
def get_capm_asset(
    ticker: str,
    start: str,
    end: str,
    benchmark_ticker: str | None = None,
    base_currency: str = "USD",
    mode: str = "general",
) -> Any:
    params = {
        "start": start,
        "end": end,
        "base_currency": base_currency,
        "mode": mode,
    }
    if benchmark_ticker:
        params["benchmark_ticker"] = benchmark_ticker

    return _get(f"/api/v1/capm/{ticker}", params=params)


def post_capm_portfolio(payload: dict) -> Any:
    return _post("/api/v1/capm/portfolio", payload)


# =========================
# VaR / CVaR
# =========================
def post_portfolio_var(payload: dict) -> Any:
    return _post("/api/v1/risk/var", payload)


# =========================
# Markowitz / Portfolio
# =========================
def post_efficient_frontier(payload: dict) -> Any:
    return _post("/api/v1/portfolio/efficient-frontier", payload)


# =========================
# Macro
# =========================
def get_macro_snapshot(base_currency: str = "USD") -> Any:
    return _get("/api/v1/macro/", params={"base_currency": base_currency})


def get_macro_fx_spot(base_currency: str) -> Any:
    return _get(f"/api/v1/macro/fx-spot/{base_currency}")


# =========================
# Benchmark
# =========================
def post_benchmark_compare(payload: dict) -> Any:
    return _post("/api/v1/benchmark/compare", payload)


# =========================
# Investor
# =========================
def post_investor_preferences(payload: dict) -> Any:
    return _post("/api/v1/investor/preferences", payload)


# =========================
# Decision panel
# =========================
def post_decision_panel(payload: dict) -> Any:
    return _post("/api/v1/decision/panel", payload)