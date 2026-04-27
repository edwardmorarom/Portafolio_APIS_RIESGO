from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests
import streamlit as st


@dataclass(frozen=True)
class ApiConfig:
    base_url: str
    api_prefix: str = "/api/v1"
    timeout: int = 120
    internal_api_key: str | None = None

    @property
    def api_root(self) -> str:
        return f"{self.base_url.rstrip('/')}{self.api_prefix}"


def _read_secret(key: str, default: str | None = None) -> str | None:
    try:
        if key in st.secrets:
            value = st.secrets[key]
            return str(value) if value is not None else default
    except Exception:
        pass

    value = os.getenv(key, default)
    return str(value) if value is not None else None


@st.cache_resource
def get_api_config() -> ApiConfig:
    base_url = _read_secret("BACKEND_BASE_URL", "http://127.0.0.1:8000")
    api_prefix = _read_secret("BACKEND_API_PREFIX", "/api/v1")
    timeout_raw = _read_secret("BACKEND_TIMEOUT_SECONDS", "120")
    internal_api_key = _read_secret("INTERNAL_API_KEY", None)

    try:
        timeout = int(timeout_raw) if timeout_raw is not None else 30
    except ValueError:
        timeout = 30

    return ApiConfig(
        base_url=base_url or "http://127.0.0.1:8000",
        api_prefix=api_prefix or "/api/v1",
        timeout=timeout,
        internal_api_key=internal_api_key,
    )


class ApiClientError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}


class ApiClient:
    def __init__(self, config: ApiConfig | None = None) -> None:
        self.config = config or get_api_config()

    def _headers(self, include_api_key: bool = False) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if include_api_key and self.config.internal_api_key:
            headers["x-api-key"] = self.config.internal_api_key

        return headers

    def _url(self, path: str) -> str:
        path = path if path.startswith("/") else f"/{path}"
        return f"{self.config.api_root}{path}"

    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.ok:
            return data

        detail = data.get("detail", {})
        if isinstance(detail, dict):
            message = detail.get("message") or detail.get("error_code") or response.text
        else:
            message = str(detail) if detail else response.text

        raise ApiClientError(
            message=message or "Error desconocido al consumir la API.",
            status_code=response.status_code,
            payload=data,
        )

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        include_api_key: bool = False,
    ) -> dict[str, Any]:
        response = requests.get(
            self._url(path),
            params=params or {},
            headers=self._headers(include_api_key=include_api_key),
            timeout=self.config.timeout,
        )
        return self._handle_response(response)

    def post(
        self,
        path: str,
        json_payload: dict[str, Any] | None = None,
        include_api_key: bool = False,
    ) -> dict[str, Any]:
        response = requests.post(
            self._url(path),
            json=json_payload or {},
            headers=self._headers(include_api_key=include_api_key),
            timeout=self.config.timeout,
        )
        return self._handle_response(response)

    # ---------- Root / health ----------
    def get_root(self) -> dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}/"
        response = requests.get(url, timeout=self.config.timeout)
        return self._handle_response(response)

    def get_health(self) -> dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}/health"
        response = requests.get(url, timeout=self.config.timeout)
        return self._handle_response(response)

    # ---------- Assets ----------
    def get_assets(self) -> dict[str, Any]:
        return self.get("/assets/")

    def search_assets(self, query: str) -> dict[str, Any]:
        return self.get("/assets/search", params={"query": query})

    # ---------- Help ----------
    def get_help_catalog(self) -> dict[str, Any]:
        return self.get("/help/catalog")

    # ---------- Market ----------
    def get_prices(self, ticker: str, start: str, end: str) -> dict[str, Any]:
        return self.get(
            f"/market/prices/{ticker}",
            params={"start": start, "end": end},
        )

    def get_returns(self, ticker: str, start: str, end: str) -> dict[str, Any]:
        return self.get(
            f"/market/returns/{ticker}",
            params={"start": start, "end": end},
        )

    # ---------- Technical ----------
    def get_technical_indicators(
        self,
        ticker: str,
        start: str,
        end: str,
        sma_window: int = 20,
        ema_window: int = 20,
        rsi_window: int = 14,
        bb_window: int = 20,
        stoch_window: int = 14,
    ) -> dict[str, Any]:
        return self.get(
            f"/technical/indicators/{ticker}",
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

    # ---------- Returns stats ----------
    def get_returns_stats(
        self,
        ticker: str,
        start: str,
        end: str,
        return_type: str = "log",
        mode: str = "general",
    ) -> dict[str, Any]:
        return self.get(
            f"/returns-stats/summary/{ticker}",
            params={
                "start": start,
                "end": end,
                "return_type": return_type,
                "mode": mode,
            },
        )

    # ---------- Alerts ----------
    def get_alerts(
        self,
        ticker: str,
        start: str,
        end: str,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0,
        stoch_overbought: float = 80.0,
        stoch_oversold: float = 20.0,
    ) -> dict[str, Any]:
        return self.get(
            f"/alerts/{ticker}",
            params={
                "start": start,
                "end": end,
                "rsi_overbought": rsi_overbought,
                "rsi_oversold": rsi_oversold,
                "stoch_overbought": stoch_overbought,
                "stoch_oversold": stoch_oversold,
            },
        )

    # ---------- GARCH ----------
    def get_garch(
        self,
        ticker: str,
        start: str,
        end: str,
        return_type: str = "log",
        mode: str = "general",
        forecast_horizon: int = 5,
    ) -> dict[str, Any]:
        return self.get(
            f"/garch/{ticker}",
            params={
                "start": start,
                "end": end,
                "return_type": return_type,
                "mode": mode,
                "forecast_horizon": forecast_horizon,
            },
        )

    # ---------- CAPM ----------
    def get_capm(
        self,
        ticker: str,
        start: str,
        end: str,
        benchmark_ticker: str | None = None,
        base_currency: str = "USD",
        return_type: str = "log",
        mode: str = "general",
    ) -> dict[str, Any]:
        params = {
            "start": start,
            "end": end,
            "base_currency": base_currency,
            "return_type": return_type,
            "mode": mode,
        }
        if benchmark_ticker:
            params["benchmark_ticker"] = benchmark_ticker

        return self.get(f"/capm/{ticker}", params=params)

    def get_portfolio_capm(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.post("/capm/portfolio", json_payload=payload, include_api_key=True)

    # ---------- Risk ----------
    def post_var_risk(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.post("/risk/var", json_payload=payload, include_api_key=True)

    def get_portfolio_var(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.post_var_risk(payload)

    # ---------- Portfolio ----------
    def post_efficient_frontier(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.post(
            "/portfolio/efficient-frontier",
            json_payload=payload,
            include_api_key=True,
        )

    def get_efficient_frontier(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.post_efficient_frontier(payload)

    # ---------- Macro ----------
    def get_macro(self, base_currency: str = "USD") -> dict[str, Any]:
        return self.get("/macro/", params={"base_currency": base_currency})

    def get_macro_snapshot(self, base_currency: str = "USD") -> dict[str, Any]:
        return self.get_macro(base_currency=base_currency)

    def get_fx_spot(self, base_currency: str = "USD") -> dict[str, Any]:
        return self.get(f"/macro/fx-spot/{base_currency}")

    # ---------- Benchmark ----------
    def post_benchmark_compare(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.post(
            "/benchmark/compare",
            json_payload=payload,
            include_api_key=True,
        )

    def compare_benchmark(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.post_benchmark_compare(payload)

    # ---------- Decision ----------
    def get_decision_panel(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.post(
            "/decision/panel",
            json_payload=payload,
            include_api_key=True,
        )

    # ---------- Investor ----------
    def validate_investor_preferences(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.post(
            "/investor/preferences",
            json_payload=payload,
            include_api_key=True,
        )


@st.cache_resource
def get_api_client() -> ApiClient:
    return ApiClient()