from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Asset, Price


class PerriOptimizerService:
    """
    Optimizador institucional de Perri.

    Calcula portafolios exactos de 5, 10 y 15 activos para:
    - Menor riesgo.
    - Máximo Sharpe.
    - Máxima rentabilidad.

    Los resultados sirven como umbrales de comparación para el módulo Markowitz.
    """

    ALLOWED_ASSET_TYPES = {"renta_variable", "renta_fija"}
    HORIZONS = (1, 3, 5)
    PORTFOLIO_SIZES = (5, 10, 15)
    OBJECTIVES = ("min_risk", "max_sharpe", "max_return")
    BENCHMARK_CANDIDATES = ("ACWI", "SPY")

    def __init__(
        self,
        min_observations: int = 200,
        trading_days: int = 252,
        min_weight_per_asset: float = 0.01,
        max_weight_per_asset: float = 0.35,
    ) -> None:
        self.min_observations = min_observations
        self.trading_days = trading_days
        self.min_weight_per_asset = min_weight_per_asset
        self.max_weight_per_asset = max_weight_per_asset

    def _get_end_date(self, db: Session, end: str | None) -> pd.Timestamp:
        if end is not None:
            return pd.to_datetime(end)

        max_date = db.scalar(select(func.max(Price.date)))

        if max_date is None:
            raise ValueError("No hay precios cargados en SQLite.")

        return pd.to_datetime(max_date)

    def _window_for_horizon(
        self,
        end_date: pd.Timestamp,
        horizon_years: int,
        start: str | None = None,
    ) -> tuple[pd.Timestamp, pd.Timestamp]:
        if start is not None:
            start_date = pd.to_datetime(start)
        else:
            start_date = end_date - pd.Timedelta(days=365 * horizon_years)

        return start_date, end_date

    def _load_eligible_assets(self, db: Session) -> list[Asset]:
        assets = list(
            db.scalars(
                select(Asset)
                .where(Asset.include_in_perri.is_(True))
                .where(Asset.asset_type.in_(self.ALLOWED_ASSET_TYPES))
                .order_by(Asset.ticker.asc())
            )
        )

        if not assets:
            raise ValueError("No hay activos elegibles de renta variable o renta fija para Perri.")

        return assets

    def _load_asset_by_ticker(self, db: Session, ticker: str) -> Asset | None:
        return db.scalar(select(Asset).where(Asset.ticker == ticker.strip().upper()))

    def _load_close_series(
        self,
        db: Session,
        asset: Asset,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
    ) -> pd.Series:
        prices = list(
            db.scalars(
                select(Price)
                .where(Price.asset_id == asset.id)
                .where(Price.date >= start_date.date())
                .where(Price.date <= end_date.date())
                .order_by(Price.date.asc())
            )
        )

        if not prices:
            return pd.Series(dtype=float, name=asset.ticker)

        data = {
            pd.to_datetime(price.date): float(
                price.close_usd if price.close_usd is not None else price.close
            )
            for price in prices
            if price.close_usd is not None or price.close is not None
        }

        series = pd.Series(data, name=asset.ticker).sort_index()
        return pd.to_numeric(series, errors="coerce").dropna()

    def _to_returns(self, close: pd.Series) -> pd.Series:
        if close.empty:
            return pd.Series(dtype=float, name=close.name)

        returns = close.pct_change()
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
        returns.name = close.name

        return returns

    def _build_returns_by_asset(
        self,
        db: Session,
        assets: list[Asset],
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
    ) -> dict[str, pd.Series]:
        returns_by_asset: dict[str, pd.Series] = {}

        for asset in assets:
            close = self._load_close_series(
                db=db,
                asset=asset,
                start_date=start_date,
                end_date=end_date,
            )
            returns = self._to_returns(close)

            if len(returns) >= self.min_observations:
                returns_by_asset[asset.ticker] = returns

        if not returns_by_asset:
            raise ValueError("No se pudieron construir rendimientos suficientes para Perri.")

        return returns_by_asset

    def _load_benchmark_returns(
        self,
        db: Session,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
    ) -> tuple[str | None, pd.Series]:
        for ticker in self.BENCHMARK_CANDIDATES:
            asset = self._load_asset_by_ticker(db=db, ticker=ticker)

            if asset is None:
                continue

            close = self._load_close_series(
                db=db,
                asset=asset,
                start_date=start_date,
                end_date=end_date,
            )

            returns = self._to_returns(close)

            if len(returns) >= self.min_observations:
                return ticker, returns

        return None, pd.Series(dtype=float)

    def _individual_metrics(
        self,
        returns_by_asset: dict[str, pd.Series],
        rf_annual: float,
    ) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []

        for ticker, returns in returns_by_asset.items():
            annual_return = float(returns.mean() * self.trading_days)
            annual_volatility = float(returns.std() * np.sqrt(self.trading_days))

            if annual_volatility <= 0 or not np.isfinite(annual_volatility):
                continue

            sharpe = float((annual_return - rf_annual) / annual_volatility)

            rows.append(
                {
                    "ticker": ticker,
                    "expected_return_annual": annual_return,
                    "volatility_annual": annual_volatility,
                    "sharpe": sharpe,
                    "observations": int(len(returns)),
                }
            )

        metrics = pd.DataFrame(rows)

        if metrics.empty:
            raise ValueError("No hay métricas individuales válidas para optimización.")

        return metrics

    def _candidate_sets(self, metrics: pd.DataFrame, portfolio_size: int) -> dict[str, list[str]]:
        size = int(portfolio_size)

        if len(metrics) < size:
            raise ValueError(
                f"No hay suficientes activos válidos para construir un portafolio exacto de {size} activos."
            )

        return {
            "min_risk": (
                metrics.sort_values("volatility_annual", ascending=True)
                .head(size)["ticker"]
                .tolist()
            ),
            "max_sharpe": (
                metrics.sort_values("sharpe", ascending=False)
                .head(size)["ticker"]
                .tolist()
            ),
            "max_return": (
                metrics.sort_values("expected_return_annual", ascending=False)
                .head(size)["ticker"]
                .tolist()
            ),
        }

    def _build_aligned_returns_matrix(
        self,
        tickers: list[str],
        returns_by_asset: dict[str, pd.Series],
    ) -> pd.DataFrame:
        selected = [returns_by_asset[ticker] for ticker in tickers if ticker in returns_by_asset]

        if len(selected) != len(tickers):
            raise ValueError("No todas las series seleccionadas están disponibles.")

        matrix = pd.concat(selected, axis=1).dropna()
        matrix = matrix.replace([np.inf, -np.inf], np.nan).dropna()

        if len(matrix) < self.min_observations:
            raise ValueError(
                f"La matriz alineada tiene {len(matrix)} observaciones; "
                f"se requieren al menos {self.min_observations}."
            )

        return matrix

    def _portfolio_metrics(
        self,
        weights: np.ndarray,
        mean_daily: pd.Series,
        cov_daily: pd.DataFrame,
        rf_annual: float,
    ) -> dict[str, float]:
        annual_return = float(np.sum(mean_daily.values * weights) * self.trading_days)
        annual_variance = float(weights.T @ (cov_daily.values * self.trading_days) @ weights)
        annual_volatility = float(np.sqrt(max(annual_variance, 0.0)))

        sharpe = 0.0
        if annual_volatility > 0:
            sharpe = float((annual_return - rf_annual) / annual_volatility)

        return {
            "expected_return_annual": annual_return,
            "volatility_annual": annual_volatility,
            "sharpe": sharpe,
        }

    def _capm_metrics(
        self,
        returns_matrix: pd.DataFrame,
        weights: np.ndarray,
        benchmark_ticker: str | None,
        benchmark_returns: pd.Series,
        rf_annual: float,
    ) -> dict[str, Any]:
        if benchmark_ticker is None or benchmark_returns.empty:
            return {
                "benchmark_ticker": None,
                "benchmark_status": "unavailable",
                "beta": None,
                "alpha_annual": None,
                "benchmark_return_annual": None,
            }

        portfolio_returns = pd.Series(
            returns_matrix.values @ weights,
            index=returns_matrix.index,
            name="portfolio",
        )

        aligned = pd.concat(
            [portfolio_returns, benchmark_returns.rename("benchmark")],
            axis=1,
        ).dropna()

        if len(aligned) < self.min_observations:
            return {
                "benchmark_ticker": benchmark_ticker,
                "benchmark_status": "insufficient_observations",
                "beta": None,
                "alpha_annual": None,
                "benchmark_return_annual": None,
            }

        benchmark_variance = float(aligned["benchmark"].var())

        if benchmark_variance <= 0 or not np.isfinite(benchmark_variance):
            return {
                "benchmark_ticker": benchmark_ticker,
                "benchmark_status": "invalid_variance",
                "beta": None,
                "alpha_annual": None,
                "benchmark_return_annual": None,
            }

        covariance = float(aligned["portfolio"].cov(aligned["benchmark"]))
        beta = covariance / benchmark_variance

        portfolio_return_annual = float(aligned["portfolio"].mean() * self.trading_days)
        benchmark_return_annual = float(aligned["benchmark"].mean() * self.trading_days)

        alpha_annual = portfolio_return_annual - (
            rf_annual + beta * (benchmark_return_annual - rf_annual)
        )

        return {
            "benchmark_ticker": benchmark_ticker,
            "benchmark_status": "ok",
            "beta": float(beta),
            "alpha_annual": float(alpha_annual),
            "benchmark_return_annual": benchmark_return_annual,
        }

    def _distribution_by_asset_type(
        self,
        tickers: list[str],
        weights: np.ndarray,
        asset_type_by_ticker: dict[str, str | None],
    ) -> dict[str, float]:
        distribution: dict[str, float] = {}

        for ticker, weight in zip(tickers, weights, strict=True):
            asset_type = asset_type_by_ticker.get(ticker) or "sin_clasificar"
            distribution[asset_type] = distribution.get(asset_type, 0.0) + float(weight)

        return dict(sorted(distribution.items()))

    def _weights_payload(self, tickers: list[str], weights: np.ndarray) -> list[dict[str, float | str]]:
        cleaned = np.asarray(weights, dtype=float)
        cleaned[np.abs(cleaned) < 1e-10] = 0.0

        total = float(cleaned.sum())
        if total > 0:
            cleaned = cleaned / total

        payload = [
            {
                "asset": tickers[i],
                "weight": float(cleaned[i]),
            }
            for i in range(len(tickers))
        ]

        return sorted(payload, key=lambda item: float(item["weight"]), reverse=True)

    def _optimize_once(
        self,
        returns_matrix: pd.DataFrame,
        rf_annual: float,
        objective_name: str,
        asset_type_by_ticker: dict[str, str | None],
        benchmark_ticker: str | None,
        benchmark_returns: pd.Series,
    ) -> dict:
        tickers = list(returns_matrix.columns)
        num_assets = len(tickers)

        if num_assets * self.min_weight_per_asset > 1:
            raise ValueError("El peso mínimo por activo hace inviable la suma de pesos.")

        if num_assets * self.max_weight_per_asset < 1:
            raise ValueError("El peso máximo por activo hace inviable la suma de pesos.")

        mean_daily = returns_matrix.mean()
        cov_daily = returns_matrix.cov()

        def objective(weights: np.ndarray) -> float:
            metrics = self._portfolio_metrics(
                weights=weights,
                mean_daily=mean_daily,
                cov_daily=cov_daily,
                rf_annual=rf_annual,
            )

            if objective_name == "min_risk":
                return float(metrics["volatility_annual"])

            if objective_name == "max_sharpe":
                return -float(metrics["sharpe"])

            if objective_name == "max_return":
                return -float(metrics["expected_return_annual"])

            raise ValueError(f"Objetivo no soportado: {objective_name}")

        constraints = [{"type": "eq", "fun": lambda weights: np.sum(weights) - 1.0}]
        bounds = tuple(
            (self.min_weight_per_asset, self.max_weight_per_asset)
            for _ in range(num_assets)
        )
        init_guess = np.repeat(1.0 / num_assets, num_assets)

        result = minimize(
            objective,
            init_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        if not result.success:
            raise ValueError(f"No fue posible optimizar {objective_name}: {result.message}")

        weights = np.asarray(result.x, dtype=float)
        weights[np.abs(weights) < 1e-10] = 0.0
        weights = weights / float(weights.sum())

        metrics = self._portfolio_metrics(
            weights=weights,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
        )

        capm = self._capm_metrics(
            returns_matrix=returns_matrix,
            weights=weights,
            benchmark_ticker=benchmark_ticker,
            benchmark_returns=benchmark_returns,
            rf_annual=rf_annual,
        )

        weights_payload = self._weights_payload(tickers=tickers, weights=weights)

        return {
            "objective": objective_name,
            "portfolio_size": int(num_assets),
            "selected_assets_count": int(len(weights_payload)),
            "selection_mode": "exact",
            "assets_used": tickers,
            "observations": int(len(returns_matrix)),
            "expected_return_annual": metrics["expected_return_annual"],
            "volatility_annual": metrics["volatility_annual"],
            "sharpe": metrics["sharpe"],
            "benchmark_ticker": capm["benchmark_ticker"],
            "benchmark_status": capm["benchmark_status"],
            "beta": capm["beta"],
            "alpha_annual": capm["alpha_annual"],
            "benchmark_return_annual": capm["benchmark_return_annual"],
            "constraints": {
                "long_only": True,
                "exact_assets": int(num_assets),
                "min_weight_per_asset": float(self.min_weight_per_asset),
                "max_weight_per_asset": float(self.max_weight_per_asset),
            },
            "weight_distribution_by_asset_type": self._distribution_by_asset_type(
                tickers=tickers,
                weights=weights,
                asset_type_by_ticker=asset_type_by_ticker,
            ),
            "weights": weights_payload,
            "optimization_status": str(result.message),
        }

    def _optimize_for_size(
        self,
        metrics: pd.DataFrame,
        returns_by_asset: dict[str, pd.Series],
        portfolio_size: int,
        rf_annual: float,
        asset_type_by_ticker: dict[str, str | None],
        benchmark_ticker: str | None,
        benchmark_returns: pd.Series,
    ) -> dict:
        candidates = self._candidate_sets(
            metrics=metrics,
            portfolio_size=portfolio_size,
        )

        portfolios = {}

        for objective_name, tickers in candidates.items():
            matrix = self._build_aligned_returns_matrix(
                tickers=tickers,
                returns_by_asset=returns_by_asset,
            )

            portfolios[objective_name] = self._optimize_once(
                returns_matrix=matrix,
                rf_annual=rf_annual,
                objective_name=objective_name,
                asset_type_by_ticker=asset_type_by_ticker,
                benchmark_ticker=benchmark_ticker,
                benchmark_returns=benchmark_returns,
            )

        return {
            "portfolio_size": int(portfolio_size),
            "selection_mode": "exact",
            "candidates": candidates,
            "min_risk": portfolios["min_risk"],
            "max_sharpe": portfolios["max_sharpe"],
            "max_return": portfolios["max_return"],
        }

    def _optimize_for_horizon(
        self,
        db: Session,
        assets: list[Asset],
        asset_type_by_ticker: dict[str, str | None],
        end_date: pd.Timestamp,
        horizon_years: int,
        rf_annual: float,
        start: str | None,
    ) -> dict:
        start_date, resolved_end_date = self._window_for_horizon(
            end_date=end_date,
            horizon_years=horizon_years,
            start=start,
        )

        returns_by_asset = self._build_returns_by_asset(
            db=db,
            assets=assets,
            start_date=start_date,
            end_date=resolved_end_date,
        )

        metrics = self._individual_metrics(
            returns_by_asset=returns_by_asset,
            rf_annual=rf_annual,
        )

        benchmark_ticker, benchmark_returns = self._load_benchmark_returns(
            db=db,
            start_date=start_date,
            end_date=resolved_end_date,
        )

        portfolio_sizes = {}

        for portfolio_size in self.PORTFOLIO_SIZES:
            portfolio_sizes[str(portfolio_size)] = self._optimize_for_size(
                metrics=metrics,
                returns_by_asset=returns_by_asset,
                portfolio_size=portfolio_size,
                rf_annual=rf_annual,
                asset_type_by_ticker=asset_type_by_ticker,
                benchmark_ticker=benchmark_ticker,
                benchmark_returns=benchmark_returns,
            )

        return {
            "horizon_years": int(horizon_years),
            "start": start_date.strftime("%Y-%m-%d"),
            "end": resolved_end_date.strftime("%Y-%m-%d"),
            "assets_with_valid_returns": int(len(returns_by_asset)),
            "benchmark_ticker": benchmark_ticker,
            "benchmark_status": "ok" if benchmark_ticker is not None else "unavailable",
            "portfolio_sizes": portfolio_sizes,
        }

    def run_optimization(
        self,
        db: Session,
        history_years: int = 5,
        rf_annual: float = 0.04,
        start: str | None = None,
        end: str | None = None,
    ) -> dict:
        end_date = self._get_end_date(db=db, end=end)

        assets = self._load_eligible_assets(db=db)
        asset_type_by_ticker = {asset.ticker: asset.asset_type for asset in assets}

        horizons: dict[str, dict] = {}

        for horizon_years in self.HORIZONS:
            horizons[f"{horizon_years}y"] = self._optimize_for_horizon(
                db=db,
                assets=assets,
                asset_type_by_ticker=asset_type_by_ticker,
                end_date=end_date,
                horizon_years=horizon_years,
                rf_annual=rf_annual,
                start=start,
            )

        primary_horizon_key = f"{int(history_years)}y"
        if primary_horizon_key not in horizons:
            primary_horizon_key = "5y"

        primary = horizons[primary_horizon_key]["portfolio_sizes"]["15"]

        return {
            "status": "ok",
            "methodology": (
                "Markowitz sobre precios persistidos en SQLite, base USD, universo Perri "
                "renta variable y renta fija. Calcula portafolios exactos de 5, 10 y 15 "
                "activos para menor riesgo, máximo Sharpe y máxima rentabilidad."
            ),
            "requested_history_years": int(history_years),
            "history_years": int(history_years),
            "rf_annual": float(rf_annual),
            "eligible_assets": int(len(assets)),
            "allowed_asset_types": sorted(self.ALLOWED_ASSET_TYPES),
            "portfolio_sizes": list(self.PORTFOLIO_SIZES),
            "objectives": list(self.OBJECTIVES),
            "horizon_keys": list(horizons.keys()),
            "benchmark_candidates": list(self.BENCHMARK_CANDIDATES),
            "min_weight_per_asset": float(self.min_weight_per_asset),
            "max_weight_per_asset": float(self.max_weight_per_asset),
            "asset_type_distribution": {
                asset_type: list(asset_type_by_ticker.values()).count(asset_type)
                for asset_type in sorted(set(asset_type_by_ticker.values()))
            },
            "horizons": horizons,
            "assets_with_valid_returns": int(
                horizons[primary_horizon_key]["assets_with_valid_returns"]
            ),
            "start": horizons[primary_horizon_key]["start"],
            "end": horizons[primary_horizon_key]["end"],
            "min_risk": primary["min_risk"],
            "max_sharpe": primary["max_sharpe"],
            "max_return": primary["max_return"],
        }
