from __future__ import annotations

import numpy as np
import pandas as pd

from app.clients.market_client import MarketClient


class PortfolioService:
    def __init__(self, client: MarketClient) -> None:
        self.client = client

    def _build_returns_matrix(self, tickers: list[str], start: str, end: str, return_type: str) -> pd.DataFrame:
        series_list: list[pd.Series] = []

        for ticker in tickers:
            df = self.client.get_prices(ticker=ticker, start=start, end=end)
            if df.empty or "Close" not in df.columns:
                continue

            close = pd.to_numeric(df["Close"], errors="coerce").dropna()

            if return_type == "log":
                ret = np.log(close / close.shift(1)).dropna()
            else:
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
            return pd.DataFrame(columns=["volatility", "return", "sharpe"])

        df = sim_df[["volatility", "return", "sharpe"]].dropna().copy()
        if df.empty:
            return pd.DataFrame(columns=["volatility", "return", "sharpe"])

        n_unique = int(df["volatility"].nunique())
        n_bins_eff = min(n_bins, max(2, n_unique))

        df["bin"] = pd.cut(df["volatility"], bins=n_bins_eff, duplicates="drop")
        df = df.dropna(subset=["bin"])

        if df.empty:
            return pd.DataFrame(columns=["volatility", "return", "sharpe"])

        frontier = (
            df.groupby("bin", observed=True, group_keys=False)
            .apply(lambda x: x.loc[x["return"].idxmax()])
            .reset_index(drop=True)
            .sort_values("volatility")
        )

        frontier["cummax_return"] = frontier["return"].cummax()
        frontier = frontier[frontier["return"] >= frontier["cummax_return"]]

        return frontier[["volatility", "return", "sharpe"]].dropna()

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

    def _closest_target_return(self, sim_df: pd.DataFrame, target_return_annual: float) -> dict | None:
        if sim_df.empty:
            return None

        df = sim_df.copy()
        df["distance_to_target"] = (df["return"] - target_return_annual).abs()
        row = df.loc[df["distance_to_target"].idxmin()]

        return {
            "target_return_annual": float(target_return_annual),
            "achieved_return_annual": float(row["return"]),
            "volatility_annual": float(row["volatility"]),
            "weights": self._extract_weights(row),
        }

    def _profile_suggestion(self, sim_df: pd.DataFrame, profile: str | None) -> dict | None:
        if sim_df.empty or profile is None:
            return None

        profile = profile.lower()

        if profile == "minimo_riesgo":
            row = sim_df.loc[sim_df["volatility"].idxmin()]
        elif profile == "maxima_utilidad":
            row = sim_df.loc[sim_df["return"].idxmax()]
        elif profile == "conservador":
            eligible = sim_df.sort_values(["volatility", "return"], ascending=[True, False]).head(200)
            row = eligible.loc[eligible["sharpe"].idxmax()] if not eligible.empty else sim_df.loc[sim_df["volatility"].idxmin()]
        elif profile == "arriesgado":
            eligible = sim_df.sort_values("return", ascending=False).head(200)
            row = eligible.loc[eligible["sharpe"].idxmax()] if not eligible.empty else sim_df.loc[sim_df["return"].idxmax()]
        else:
            return None

        return {
            "profile": profile,
            "return": float(row["return"]),
            "volatility": float(row["volatility"]),
            "sharpe": float(row["sharpe"]),
            "weights": self._extract_weights(row),
        }

    def build_efficient_frontier(
        self,
        tickers: list[str],
        start: str,
        end: str,
        rf_annual: float,
        n_portfolios: int,
        return_type: str,
        target_return_annual: float | None = None,
        risk_profile: str | None = None,
    ) -> dict:
        returns_df = self._build_returns_matrix(tickers=tickers, start=start, end=end, return_type=return_type)

        if returns_df.empty:
            raise ValueError("No fue posible construir la matriz de rendimientos.")

        if len(returns_df.columns) != len(tickers):
            raise ValueError("No fue posible obtener datos válidos para todos los tickers enviados.")

        if len(returns_df) < self.client.settings.min_obs_portfolio:
            raise ValueError(
                f"Se requieren al menos {self.client.settings.min_obs_portfolio} observaciones para optimización."
            )

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

        target_return_portfolio = (
            self._closest_target_return(sim_df, target_return_annual)
            if target_return_annual is not None
            else None
        )
        suggested_profile_portfolio = self._profile_suggestion(sim_df, risk_profile)

        corr_df = returns_df.corr().round(6)

        return {
            "tickers": [t.upper() for t in tickers],
            "start": start,
            "end": end,
            "rf_annual": float(rf_annual),
            "frontier": frontier_df.to_dict(orient="records"),
            "simulated_portfolios": sim_df[["volatility", "return", "sharpe"]].to_dict(orient="records"),
            "correlation_matrix": corr_df.to_dict(),
            "observations": int(len(returns_df)),
            "n_assets": int(returns_df.shape[1]),
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
            "target_return_portfolio": target_return_portfolio,
            "suggested_profile_portfolio": suggested_profile_portfolio,
        }