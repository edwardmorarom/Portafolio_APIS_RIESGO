from __future__ import annotations

import numpy as np
import pandas as pd

from app.clients.market_client import MarketClient
from app.services.macro_service import MacroService


class BenchmarkService:
    def __init__(self, market_client: MarketClient, macro_service: MacroService) -> None:
        self.market_client = market_client
        self.macro_service = macro_service

    def _returns(self, ticker: str, start: str, end: str, return_type: str) -> pd.Series:
        df = self.market_client.get_prices(ticker=ticker, start=start, end=end)
        if df.empty or "Close" not in df.columns:
            return pd.Series(dtype=float)

        close = pd.to_numeric(df["Close"], errors="coerce").dropna()

        if return_type == "log":
            ret = np.log(close / close.shift(1)).dropna()
        else:
            ret = close.pct_change().dropna()

        ret.name = ticker.upper()
        return ret

    def _returns_matrix(self, tickers: list[str], start: str, end: str, return_type: str) -> pd.DataFrame:
        series_list: list[pd.Series] = []

        for ticker in tickers:
            s = self._returns(ticker=ticker, start=start, end=end, return_type=return_type)
            if not s.empty:
                series_list.append(s)

        if not series_list:
            return pd.DataFrame()

        return pd.concat(series_list, axis=1).dropna()

    def _cumulative_return(self, returns: pd.Series, return_type: str) -> float:
        if return_type == "log":
            return float(np.exp(returns.sum()) - 1.0)
        return float((1.0 + returns).prod() - 1.0)

    def _annual_return(self, returns: pd.Series, return_type: str) -> float:
        if return_type == "log":
            return float(np.exp(returns.mean() * 252) - 1.0)
        return float(returns.mean() * 252)

    def _annual_volatility(self, returns: pd.Series) -> float:
        return float(returns.std(ddof=1) * np.sqrt(252))

    def _max_drawdown(self, returns: pd.Series, return_type: str) -> float:
        if return_type == "log":
            wealth = np.exp(returns.cumsum())
        else:
            wealth = (1.0 + returns).cumprod()

        running_max = wealth.cummax()
        drawdown = wealth / running_max - 1.0
        return float(drawdown.min())

    def _metrics(self, returns: pd.Series, rf_decimal: float, return_type: str) -> dict:
        annual_return = self._annual_return(returns, return_type=return_type)
        annual_vol = self._annual_volatility(returns)
        sharpe = 0.0 if annual_vol <= 0 else float((annual_return - rf_decimal) / annual_vol)

        return {
            "cumulative_return": self._cumulative_return(returns, return_type=return_type),
            "annual_return": annual_return,
            "annual_volatility": annual_vol,
            "sharpe": sharpe,
            "max_drawdown": self._max_drawdown(returns, return_type=return_type),
        }

    def compare(
        self,
        tickers: list[str],
        weights: list[float],
        benchmark_ticker: str,
        base_currency: str,
        start: str,
        end: str,
        return_type: str,
        mode: str,
    ) -> dict:
        returns_df = self._returns_matrix(tickers=tickers, start=start, end=end, return_type=return_type)
        benchmark_ret = self._returns(ticker=benchmark_ticker, start=start, end=end, return_type=return_type)

        if returns_df.empty:
            raise ValueError("No fue posible construir la matriz de rendimientos del portafolio.")
        if len(returns_df.columns) != len(tickers):
            raise ValueError("No fue posible obtener datos válidos para todos los tickers enviados.")
        if benchmark_ret.empty:
            raise ValueError(f"No se encontraron rendimientos para el benchmark {benchmark_ticker}.")

        joined = pd.concat([returns_df, benchmark_ret], axis=1).dropna()
        if joined.empty or len(joined) < self.market_client.settings.min_obs_portfolio:
            raise ValueError("No hay suficientes observaciones comunes para comparar contra benchmark.")

        portfolio_returns = joined.iloc[:, :-1] @ np.asarray(weights, dtype=float)
        bench_returns = joined.iloc[:, -1]

        rf_ticker, rf_pct = self.macro_service.resolve_rf_inputs(base_currency=base_currency)
        rf_decimal = rf_pct / 100.0

        portfolio_metrics = self._metrics(portfolio_returns, rf_decimal=rf_decimal, return_type=return_type)
        benchmark_metrics = self._metrics(bench_returns, rf_decimal=rf_decimal, return_type=return_type)

        var_bench = float(bench_returns.var(ddof=1))
        beta = 0.0 if np.isclose(var_bench, 0.0) else float(portfolio_returns.cov(bench_returns) / var_bench)
        alpha_jensen = portfolio_metrics["annual_return"] - (
            rf_decimal + beta * (benchmark_metrics["annual_return"] - rf_decimal)
        )

        active_returns = portfolio_returns - bench_returns
        tracking_error = float(active_returns.std(ddof=1) * np.sqrt(252))
        info_ratio = 0.0 if np.isclose(tracking_error, 0.0) else float(
            (portfolio_metrics["annual_return"] - benchmark_metrics["annual_return"]) / tracking_error
        )

        if mode == "general":
            summary = (
                f"El portafolio tuvo retorno anual de {portfolio_metrics['annual_return']:.2%} "
                f"frente a {benchmark_metrics['annual_return']:.2%} del benchmark. "
                f"El alpha de Jensen fue {alpha_jensen:.2%} y el max drawdown del portafolio "
                f"fue {portfolio_metrics['max_drawdown']:.2%}."
            )
        else:
            summary = (
                f"Portfolio annual_return={portfolio_metrics['annual_return']:.4f}, "
                f"benchmark annual_return={benchmark_metrics['annual_return']:.4f}, "
                f"alpha_jensen={alpha_jensen:.4f}, tracking_error={tracking_error:.4f}, "
                f"information_ratio={info_ratio:.4f}."
            )

        return {
            "tickers": [t.upper() for t in tickers],
            "weights": weights,
            "benchmark_ticker": benchmark_ticker.upper(),
            "base_currency": base_currency.upper(),
            "rf_ticker": rf_ticker,
            "rf_rate_pct": rf_pct,
            "portfolio": portfolio_metrics,
            "benchmark": benchmark_metrics,
            "alpha_jensen": float(alpha_jensen),
            "tracking_error": float(tracking_error),
            "information_ratio": float(info_ratio),
            "mode": mode,
            "summary": summary,
            "start": start,
            "end": end,
        }