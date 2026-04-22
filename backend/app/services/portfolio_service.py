from __future__ import annotations

import numpy as np
import pandas as pd

from app.clients.market_client import MarketClient


class PortfolioService:
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

    def _simulate_portfolios(
        self,
        returns_df: pd.DataFrame,
        rf_annual: float,
        n_portfolios: int,
    ) -> pd.DataFrame:
        rng = np.random.default_rng(42)

        mean_returns = returns_df.mean().values * 252
        cov_matrix = returns_df.cov().values * 252
        n_assets = returns_df.shape[1]

        rows = []
        for _ in range(n_portfolios):
            weights = rng.random(n_assets)
            weights = weights / weights.sum()

            port_return = float(weights @ mean_returns)
            port_vol = float(np.sqrt(weights.T @ cov_matrix @ weights))

            if not np.isfinite(port_return) or not np.isfinite(port_vol) or port_vol <= 0:
                continue

            sharpe = (port_return - rf_annual) / port_vol

            row = {
                "return": port_return,
                "volatility": port_vol,
                "sharpe": sharpe,
            }

            for idx, col in enumerate(returns_df.columns):
                row[f"w_{col}"] = float(weights[idx])

            rows.append(row)

        return pd.DataFrame(rows)

    def _efficient_frontier(self, sim_df: pd.DataFrame, n_bins: int = 50) -> pd.DataFrame:
        if sim_df.empty:
            return pd.DataFrame(columns=["volatility", "return"])

        df = sim_df[["volatility", "return"]].dropna().copy()
        if df.empty:
            return pd.DataFrame(columns=["volatility", "return"])

        n_unique = int(df["volatility"].nunique())
        n_bins_eff = min(n_bins, max(2, n_unique))

        df["bin"] = pd.cut(df["volatility"], bins=n_bins_eff, duplicates="drop")
        df = df.dropna(subset=["bin"])

        if df.empty:
            return pd.DataFrame(columns=["volatility", "return"])

        frontier = (
            df.groupby("bin", observed=True, group_keys=False)
            .apply(lambda x: x.loc[x["return"].idxmax()])
            .reset_index(drop=True)
            .sort_values("volatility")
        )

        frontier["cummax_return"] = frontier["return"].cummax()
        frontier = frontier[frontier["return"] >= frontier["cummax_return"]]

        return frontier[["volatility", "return"]].dropna()

    def _extract_weights(self, row: pd.Series) -> list[dict]:
        items = []
        for key, value in row.items():
            if key.startswith("w_"):
                items.append(
                    {
                        "asset": key.replace("w_", ""),
                        "weight": float(value),
                    }
                )
        items.sort(key=lambda x: x["weight"], reverse=True)
        return items

    def build_efficient_frontier(
        self,
        tickers: list[str],
        start: str,
        end: str,
        rf_annual: float,
        n_portfolios: int,
    ) -> dict:
        returns_df = self._build_returns_matrix(tickers=tickers, start=start, end=end)

        if returns_df.empty:
            raise ValueError("No fue posible construir la matriz de rendimientos.")

        if len(returns_df.columns) != len(tickers):
            raise ValueError("No fue posible obtener datos válidos para todos los tickers enviados.")

        sim_df = self._simulate_portfolios(
            returns_df=returns_df,
            rf_annual=rf_annual,
            n_portfolios=n_portfolios,
        )

        if sim_df.empty:
            raise ValueError("No fue posible simular portafolios.")

        frontier_df = self._efficient_frontier(sim_df)

        min_var = sim_df.loc[sim_df["volatility"].idxmin()]
        max_sharpe = sim_df.loc[sim_df["sharpe"].idxmax()]

        return {
            "tickers": tickers,
            "start": start,
            "end": end,
            "rf_annual": rf_annual,
            "frontier": frontier_df.to_dict(orient="records"),
            "min_variance": {
                "return": float(min_var["return"]),
                "volatility": float(min_var["volatility"]),
                "sharpe": float(min_var["sharpe"]),
                "weights": self._extract_weights(min_var),
            },
            "max_sharpe": {
                "return": float(max_sharpe["return"]),
                "volatility": float(max_sharpe["volatility"]),
                "sharpe": float(max_sharpe["sharpe"]),
                "weights": self._extract_weights(max_sharpe),
            },
        }