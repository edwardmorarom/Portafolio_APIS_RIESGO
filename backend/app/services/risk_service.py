from __future__ import annotations

import numpy as np
import pandas as pd

from app.clients.market_client import MarketClient


class RiskService:
    def __init__(self, client: MarketClient) -> None:
        self.client = client

    def _build_returns_matrix(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        series_list: list[pd.Series] = []

        for ticker in tickers:
            df = self.client.get_prices(ticker=ticker, start=start, end=end)
            if df.empty or "Close" not in df.columns:
                continue

            close = pd.to_numeric(df["Close"], errors="coerce").dropna()
            ret = close.pct_change().dropna()
            ret.name = ticker.upper()
            series_list.append(ret)

        if not series_list:
            return pd.DataFrame()

        returns_df = pd.concat(series_list, axis=1).dropna()
        return returns_df

    def _portfolio_returns(self, returns_df: pd.DataFrame, weights: list[float]) -> pd.Series:
        w = np.asarray(weights, dtype=float)
        port = returns_df @ w
        port.name = "portfolio_return"
        return port

    def _historical_var_cvar(self, portfolio_returns: pd.Series, alpha: float) -> dict:
        q = 1 - alpha
        cutoff = float(np.quantile(portfolio_returns, q))
        tail = portfolio_returns[portfolio_returns <= cutoff]

        var_daily = max(0.0, -cutoff)
        cvar_daily = max(var_daily, float(-tail.mean()) if len(tail) > 0 else var_daily)

        return {
            "var_daily": float(var_daily),
            "cvar_daily": float(cvar_daily),
            "var_annualized": float(var_daily * np.sqrt(252)),
            "cvar_annualized": float(cvar_daily * np.sqrt(252)),
        }

    def _monte_carlo_var_cvar(
        self,
        returns_df: pd.DataFrame,
        weights: list[float],
        alpha: float,
        n_sim: int,
    ) -> dict:
        w = np.asarray(weights, dtype=float)
        mu = returns_df.mean().values
        cov = returns_df.cov().values

        rng = np.random.default_rng(42)
        sims = rng.multivariate_normal(mu, cov, size=n_sim)
        port_sim = sims @ w

        q = 1 - alpha
        cutoff = float(np.quantile(port_sim, q))
        tail = port_sim[port_sim <= cutoff]

        var_daily = max(0.0, -cutoff)
        cvar_daily = max(var_daily, float(-tail.mean()) if len(tail) > 0 else var_daily)

        return {
            "var_daily": float(var_daily),
            "cvar_daily": float(cvar_daily),
            "var_annualized": float(var_daily * np.sqrt(252)),
            "cvar_annualized": float(cvar_daily * np.sqrt(252)),
        }

    def calculate_var(
        self,
        tickers: list[str],
        weights: list[float],
        start: str,
        end: str,
        alpha: float,
        n_sim: int,
    ) -> dict:
        returns_df = self._build_returns_matrix(tickers=tickers, start=start, end=end)

        if returns_df.empty:
            raise ValueError("No fue posible construir la matriz de rendimientos.")

        if len(returns_df.columns) != len(tickers):
            raise ValueError("No fue posible obtener datos válidos para todos los tickers enviados.")

        portfolio_returns = self._portfolio_returns(returns_df, weights)

        if portfolio_returns.empty:
            raise ValueError("No fue posible calcular los rendimientos del portafolio.")

        historical = self._historical_var_cvar(portfolio_returns, alpha=alpha)
        monte_carlo = self._monte_carlo_var_cvar(
            returns_df=returns_df,
            weights=weights,
            alpha=alpha,
            n_sim=n_sim,
        )

        return {
            "tickers": [t.upper() for t in tickers],
            "weights": weights,
            "alpha": alpha,
            "start": start,
            "end": end,
            "historical": historical,
            "monte_carlo": monte_carlo,
        }