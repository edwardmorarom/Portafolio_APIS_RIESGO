from __future__ import annotations

import numpy as np
import pandas as pd
from math import erfc, sqrt

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

    def _base100_series(
        self,
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series,
        return_type: str,
    ) -> list[dict]:
        if return_type == "log":
            portfolio_index = 100.0 * np.exp(portfolio_returns.cumsum())
            benchmark_index = 100.0 * np.exp(benchmark_returns.cumsum())
        else:
            portfolio_index = 100.0 * (1.0 + portfolio_returns).cumprod()
            benchmark_index = 100.0 * (1.0 + benchmark_returns).cumprod()

        points: list[dict] = [{"date": str(portfolio_returns.index[0].date()), "portfolio": 100.0, "benchmark": 100.0}]
        for date, port_value, bench_value in zip(
            portfolio_index.index,
            portfolio_index.to_numpy(dtype=float),
            benchmark_index.to_numpy(dtype=float),
        ):
            points.append(
                {
                    "date": str(date.date()) if hasattr(date, "date") else str(date),
                    "portfolio": float(port_value),
                    "benchmark": float(bench_value),
                }
            )
        return points

    def _alpha_significance(
        self,
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series,
        rf_decimal: float,
    ) -> dict:
        if len(portfolio_returns) < 5:
            return {"alpha_t_stat": None, "alpha_p_value": None, "alpha_significant_5pct": False}

        rf_daily = rf_decimal / 252.0
        y = (portfolio_returns - rf_daily).to_numpy(dtype=float)
        x = (benchmark_returns - rf_daily).to_numpy(dtype=float)
        x_mean = float(np.mean(x))
        y_mean = float(np.mean(y))
        ssx = float(np.sum((x - x_mean) ** 2))
        if np.isclose(ssx, 0.0):
            return {"alpha_t_stat": None, "alpha_p_value": None, "alpha_significant_5pct": False}

        beta = float(np.sum((x - x_mean) * (y - y_mean)) / ssx)
        alpha_daily = y_mean - beta * x_mean
        residuals = y - (alpha_daily + beta * x)
        dof = len(x) - 2
        if dof <= 0:
            return {"alpha_t_stat": None, "alpha_p_value": None, "alpha_significant_5pct": False}

        sigma2 = float(np.sum(residuals ** 2) / dof)
        se_alpha = float(np.sqrt(sigma2 * (1.0 / len(x) + (x_mean ** 2) / ssx)))
        if np.isclose(se_alpha, 0.0):
            return {"alpha_t_stat": None, "alpha_p_value": None, "alpha_significant_5pct": False}

        t_stat = float(alpha_daily / se_alpha)
        p_value = float(erfc(abs(t_stat) / sqrt(2.0)))
        return {
            "alpha_t_stat": t_stat,
            "alpha_p_value": p_value,
            "alpha_significant_5pct": p_value < 0.05,
        }

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
        alpha_stats = self._alpha_significance(
            portfolio_returns=portfolio_returns,
            benchmark_returns=bench_returns,
            rf_decimal=rf_decimal,
        )
        base100_series = self._base100_series(
            portfolio_returns=portfolio_returns,
            benchmark_returns=bench_returns,
            return_type=return_type,
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
                f"alpha_jensen={alpha_jensen:.4f}, beta={beta:.4f}, "
                f"alpha_t_stat={alpha_stats['alpha_t_stat']}, alpha_p_value={alpha_stats['alpha_p_value']}, "
                f"tracking_error={tracking_error:.4f}, information_ratio={info_ratio:.4f}."
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
            "beta_portfolio": float(beta),
            "alpha_t_stat": alpha_stats["alpha_t_stat"],
            "alpha_p_value": alpha_stats["alpha_p_value"],
            "alpha_significant_5pct": bool(alpha_stats["alpha_significant_5pct"]),
            "tracking_error": float(tracking_error),
            "information_ratio": float(info_ratio),
            "base100_series": base100_series,
            "mode": mode,
            "summary": summary,
            "start": start,
            "end": end,
        }
