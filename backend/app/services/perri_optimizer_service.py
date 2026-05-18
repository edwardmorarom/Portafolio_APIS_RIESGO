from __future__ import annotations

from datetime import timedelta
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

    Lee precios persistidos en SQLite y calcula:
    - Portafolio de mínimo riesgo.
    - Portafolio de mejor relación riesgo-rentabilidad, usando Sharpe.

    En esta primera versión se limita a:
    - renta_variable
    - renta_fija

    Esto evita mezclar commodities, efectivo o ETF sectoriales antes de definir
    reglas metodológicas más completas.
    """

    ALLOWED_ASSET_TYPES = {"renta_variable", "renta_fija"}

    def __init__(
        self,
        max_candidate_assets: int = 15,
        min_observations: int = 200,
        trading_days: int = 252,
    ) -> None:
        self.max_candidate_assets = max_candidate_assets
        self.min_observations = min_observations
        self.trading_days = trading_days

    def _get_date_window(
        self,
        db: Session,
        history_years: int,
        start: str | None,
        end: str | None,
    ) -> tuple[pd.Timestamp, pd.Timestamp]:
        if end is not None:
            end_date = pd.to_datetime(end)
        else:
            max_date = db.scalar(select(func.max(Price.date)))

            if max_date is None:
                raise ValueError("No hay precios cargados en SQLite.")

            end_date = pd.to_datetime(max_date)

        if start is not None:
            start_date = pd.to_datetime(start)
        else:
            start_date = end_date - pd.Timedelta(days=365 * history_years)

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
        series = pd.to_numeric(series, errors="coerce").dropna()

        return series

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

            if close.empty:
                continue

            returns = close.pct_change().replace([np.inf, -np.inf], np.nan).dropna()

            if len(returns) >= self.min_observations:
                returns_by_asset[asset.ticker] = returns

        if not returns_by_asset:
            raise ValueError("No se pudieron construir rendimientos suficientes para Perri.")

        return returns_by_asset

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

    def _build_aligned_returns_matrix(
        self,
        tickers: list[str],
        returns_by_asset: dict[str, pd.Series],
    ) -> pd.DataFrame:
        selected = [
            returns_by_asset[ticker]
            for ticker in tickers
            if ticker in returns_by_asset
        ]

        if not selected:
            raise ValueError("No hay series seleccionadas para construir matriz de retornos.")

        matrix = pd.concat(selected, axis=1).dropna()
        matrix = matrix.replace([np.inf, -np.inf], np.nan).dropna()

        if matrix.empty:
            raise ValueError("La matriz alineada de rendimientos quedó vacía.")

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

    def _optimize(
        self,
        returns_matrix: pd.DataFrame,
        rf_annual: float,
        objective_name: str,
    ) -> dict:
        tickers = list(returns_matrix.columns)
        num_assets = len(tickers)

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

            raise ValueError(f"Objetivo no soportado: {objective_name}")

        constraints = [{"type": "eq", "fun": lambda weights: np.sum(weights) - 1.0}]
        bounds = tuple((0.0, 1.0) for _ in range(num_assets))
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
        metrics = self._portfolio_metrics(
            weights=weights,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
        )

        weights_payload = [
            {
                "asset": tickers[i],
                "weight": float(weights[i]),
            }
            for i in range(num_assets)
            if float(weights[i]) > 0.0001
        ]

        weights_payload = sorted(
            weights_payload,
            key=lambda item: item["weight"],
            reverse=True,
        )

        return {
            "objective": objective_name,
            "assets_used": tickers,
            "observations": int(len(returns_matrix)),
            "expected_return_annual": metrics["expected_return_annual"],
            "volatility_annual": metrics["volatility_annual"],
            "sharpe": metrics["sharpe"],
            "weights": weights_payload,
            "optimization_status": str(result.message),
        }

    def run_optimization(
        self,
        db: Session,
        history_years: int = 5,
        rf_annual: float = 0.04,
        start: str | None = None,
        end: str | None = None,
    ) -> dict:
        start_date, end_date = self._get_date_window(
            db=db,
            history_years=history_years,
            start=start,
            end=end,
        )

        assets = self._load_eligible_assets(db=db)
        asset_type_by_ticker = {asset.ticker: asset.asset_type for asset in assets}

        returns_by_asset = self._build_returns_by_asset(
            db=db,
            assets=assets,
            start_date=start_date,
            end_date=end_date,
        )

        metrics = self._individual_metrics(
            returns_by_asset=returns_by_asset,
            rf_annual=rf_annual,
        )

        min_risk_candidates = (
            metrics.sort_values("volatility_annual", ascending=True)
            .head(self.max_candidate_assets)["ticker"]
            .tolist()
        )

        max_sharpe_candidates = (
            metrics.sort_values("sharpe", ascending=False)
            .head(self.max_candidate_assets)["ticker"]
            .tolist()
        )

        min_risk_matrix = self._build_aligned_returns_matrix(
            tickers=min_risk_candidates,
            returns_by_asset=returns_by_asset,
        )

        max_sharpe_matrix = self._build_aligned_returns_matrix(
            tickers=max_sharpe_candidates,
            returns_by_asset=returns_by_asset,
        )

        min_risk = self._optimize(
            returns_matrix=min_risk_matrix,
            rf_annual=rf_annual,
            objective_name="min_risk",
        )

        max_sharpe = self._optimize(
            returns_matrix=max_sharpe_matrix,
            rf_annual=rf_annual,
            objective_name="max_sharpe",
        )

        return {
            "status": "ok",
            "methodology": "Markowitz sobre precios persistidos en SQLite, base USD, universo Perri renta variable y renta fija.",
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "history_years": int(history_years),
            "rf_annual": float(rf_annual),
            "eligible_assets": int(len(assets)),
            "assets_with_valid_returns": int(len(returns_by_asset)),
            "max_candidate_assets": int(self.max_candidate_assets),
            "allowed_asset_types": sorted(self.ALLOWED_ASSET_TYPES),
            "asset_type_distribution": {
                asset_type: list(asset_type_by_ticker.values()).count(asset_type)
                for asset_type in sorted(set(asset_type_by_ticker.values()))
            },
            "min_risk_candidates": min_risk_candidates,
            "max_sharpe_candidates": max_sharpe_candidates,
            "min_risk": min_risk,
            "max_sharpe": max_sharpe,
        }
