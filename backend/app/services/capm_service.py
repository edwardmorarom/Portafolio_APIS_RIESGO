from __future__ import annotations

import numpy as np
import pandas as pd

from app.clients.market_client import MarketClient
from app.services.macro_service import MacroService


class CapmService:
    def __init__(self, market_client: MarketClient, macro_service: MacroService) -> None:
        self.market_client = market_client
        self.macro_service = macro_service

    def _returns(self, ticker: str, start: str, end: str) -> pd.Series:
        df = self.market_client.get_prices(ticker=ticker, start=start, end=end)
        if df.empty or "Close" not in df.columns:
            return pd.Series(dtype=float)

        close = pd.to_numeric(df["Close"], errors="coerce").dropna()
        ret = close.pct_change().dropna()
        ret.name = ticker.upper()
        return ret

    def _returns_matrix(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        series_list: list[pd.Series] = []

        for ticker in tickers:
            s = self._returns(ticker=ticker, start=start, end=end)
            if not s.empty:
                series_list.append(s)

        if not series_list:
            return pd.DataFrame()

        return pd.concat(series_list, axis=1).dropna()

    def calculate_capm(
        self,
        ticker: str,
        benchmark_ticker: str,
        base_currency: str,
        start: str,
        end: str,
    ) -> dict:
        asset_ret = self._returns(ticker=ticker, start=start, end=end)
        bench_ret = self._returns(ticker=benchmark_ticker, start=start, end=end)

        if asset_ret.empty:
            raise ValueError(f"No se encontraron rendimientos para el activo {ticker}.")
        if bench_ret.empty:
            raise ValueError(f"No se encontraron rendimientos para el benchmark {benchmark_ticker}.")

        joined = pd.concat([asset_ret, bench_ret], axis=1).dropna()
        if joined.empty or joined.shape[0] < 30:
            raise ValueError("No hay suficientes observaciones comunes entre activo y benchmark.")

        asset_series = joined.iloc[:, 0]
        bench_series = joined.iloc[:, 1]

        var_bench = float(bench_series.var(ddof=1))
        if np.isclose(var_bench, 0.0):
            raise ValueError("La varianza del benchmark es cero o casi cero.")

        cov = float(asset_series.cov(bench_series))
        beta = cov / var_bench

        asset_return_annual = float(asset_series.mean() * 252)
        benchmark_return_annual = float(bench_series.mean() * 252)

        rf_ticker, rf_pct = self.macro_service.resolve_rf_inputs(base_currency=base_currency)
        rf_decimal = rf_pct / 100.0

        capm_expected_return = rf_decimal + beta * (benchmark_return_annual - rf_decimal)
        alpha_simple = asset_return_annual - capm_expected_return

        return {
            "ticker": ticker.upper(),
            "benchmark_ticker": benchmark_ticker.upper(),
            "base_currency": base_currency.upper(),
            "rf_ticker": rf_ticker,
            "rf_rate_pct": rf_pct,
            "beta": float(beta),
            "asset_return_annual": asset_return_annual,
            "benchmark_return_annual": benchmark_return_annual,
            "capm_expected_return": float(capm_expected_return),
            "alpha_simple": float(alpha_simple),
            "start": start,
            "end": end,
        }

    def calculate_portfolio_capm(
        self,
        tickers: list[str],
        weights: list[float],
        benchmark_ticker: str,
        base_currency: str,
        start: str,
        end: str,
    ) -> dict:
        returns_df = self._returns_matrix(tickers=tickers, start=start, end=end)
        bench_ret = self._returns(ticker=benchmark_ticker, start=start, end=end)

        if returns_df.empty:
            raise ValueError("No fue posible construir la matriz de rendimientos del portafolio.")
        if len(returns_df.columns) != len(tickers):
            raise ValueError("No fue posible obtener datos válidos para todos los tickers enviados.")
        if bench_ret.empty:
            raise ValueError(f"No se encontraron rendimientos para el benchmark {benchmark_ticker}.")

        joined = pd.concat([returns_df, bench_ret], axis=1).dropna()
        if joined.empty or joined.shape[0] < 30:
            raise ValueError("No hay suficientes observaciones comunes entre portafolio y benchmark.")

        portfolio_returns = joined.iloc[:, :-1] @ np.asarray(weights, dtype=float)
        benchmark_returns = joined.iloc[:, -1]

        var_bench = float(benchmark_returns.var(ddof=1))
        if np.isclose(var_bench, 0.0):
            raise ValueError("La varianza del benchmark es cero o casi cero.")

        cov = float(portfolio_returns.cov(benchmark_returns))
        portfolio_beta = cov / var_bench

        portfolio_return_annual = float(portfolio_returns.mean() * 252)
        benchmark_return_annual = float(benchmark_returns.mean() * 252)

        rf_ticker, rf_pct = self.macro_service.resolve_rf_inputs(base_currency=base_currency)
        rf_decimal = rf_pct / 100.0

        capm_expected_return = rf_decimal + portfolio_beta * (benchmark_return_annual - rf_decimal)
        alpha_simple = portfolio_return_annual - capm_expected_return

        return {
            "tickers": [t.upper() for t in tickers],
            "weights": weights,
            "benchmark_ticker": benchmark_ticker.upper(),
            "base_currency": base_currency.upper(),
            "rf_ticker": rf_ticker,
            "rf_rate_pct": rf_pct,
            "portfolio_beta": float(portfolio_beta),
            "portfolio_return_annual": portfolio_return_annual,
            "benchmark_return_annual": benchmark_return_annual,
            "capm_expected_return": float(capm_expected_return),
            "alpha_simple": float(alpha_simple),
            "start": start,
            "end": end,
        }