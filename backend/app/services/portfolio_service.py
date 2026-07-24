from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from app.clients.market_client import MarketClient


class PortfolioOptimizerSingleton:
    """
    Implementación del patrón Singleton para el optimizador usado por el Robo-Advisor.
    Mantiene caché de matrices de rendimientos para evitar recálculos costosos.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PortfolioOptimizerSingleton, cls).__new__(cls)
            cls._instance._cache = {}
        return cls._instance

    def __init__(self, client: MarketClient | None = None):
        if not hasattr(self, "initialized"):
            self.client = client
            self.initialized = True
        elif client is not None:
            self.client = client

    def _get_returns_matrix(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        if self.client is None:
            raise ValueError("PortfolioOptimizerSingleton requiere un MarketClient válido.")

        clean_tickers = [ticker.strip().upper() for ticker in tickers if ticker.strip()]
        cache_key = f"{','.join(sorted(clean_tickers))}_{start}_{end}_simple"

        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        series_list: list[pd.Series] = []

        for ticker in clean_tickers:
            df = self.client.get_prices(ticker=ticker, start=start, end=end)

            if df.empty or "Close" not in df.columns:
                continue

            close = pd.to_numeric(df["Close"], errors="coerce").dropna()
            returns = close.pct_change().dropna()
            returns.name = ticker
            series_list.append(returns)

        if not series_list:
            raise ValueError("No se pudieron obtener datos para los tickers solicitados.")

        returns_matrix = pd.concat(series_list, axis=1).dropna()

        if returns_matrix.empty:
            raise ValueError("No se pudo construir una matriz de rendimientos válida.")

        self._cache[cache_key] = returns_matrix.copy()
        return returns_matrix.copy()

    def optimize_markowitz(
        self,
        tickers: list[str],
        start: str,
        end: str,
        target_return: float | None = None,
    ) -> dict:
        """
        Optimiza un portafolio minimizando la varianza.
        Si target_return existe, minimiza la varianza sujeto a ese retorno objetivo.
        Este método se conserva para compatibilidad con RoboAdvisorService.
        """
        returns = self._get_returns_matrix(tickers=tickers, start=start, end=end)

        effective_tickers = list(returns.columns)
        mean_returns = returns.mean() * 252
        cov_matrix = returns.cov() * 252
        num_assets = len(effective_tickers)

        def portfolio_volatility(weights: np.ndarray) -> float:
            return float(np.sqrt(weights.T @ cov_matrix.values @ weights))

        constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]

        if target_return is not None:
            constraints.append(
                {
                    "type": "eq",
                    "fun": lambda x: float(np.sum(mean_returns.values * x) - target_return),
                }
            )

        bounds = tuple((0.0, 1.0) for _ in range(num_assets))
        init_guess = np.repeat(1.0 / num_assets, num_assets)

        optimized = minimize(
            portfolio_volatility,
            init_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        if not optimized.success:
            raise ValueError(f"No fue posible optimizar el portafolio: {optimized.message}")

        opt_weights = np.asarray(optimized.x, dtype=float)
        opt_return = float(np.sum(mean_returns.values * opt_weights))
        opt_risk = float(portfolio_volatility(opt_weights))
        sharpe_ratio = float(opt_return / opt_risk) if opt_risk > 0 else 0.0

        return {
            "weights": {
                effective_tickers[i]: float(opt_weights[i])
                for i in range(num_assets)
            },
            "expected_return_annual": opt_return,
            "volatility_annual": opt_risk,
            "sharpe_ratio": sharpe_ratio,
            "optimization_status": str(optimized.message),
        }


class PortfolioService:
    """
    Servicio principal de Markowitz usado por:
    - /api/v1/portfolio/efficient-frontier
    - DecisionService
    - Dashboard de Markowitz

    Construye frontera eficiente, nube de portafolios simulados,
    matriz de correlación y portafolios óptimos.
    """

    def __init__(self, client: MarketClient) -> None:
        self.client = client

    def _returns_by_type(self, close: pd.Series, return_type: str) -> pd.Series:
        close = pd.to_numeric(close, errors="coerce").dropna()

        if return_type == "log":
            returns = np.log(close / close.shift(1)).dropna()
        else:
            returns = close.pct_change().dropna()

        return returns.replace([np.inf, -np.inf], np.nan).dropna()

    def _build_returns_matrix(
        self,
        tickers: list[str],
        start: str,
        end: str,
        return_type: str,
    ) -> pd.DataFrame:
        clean_tickers = [ticker.strip().upper() for ticker in tickers if ticker.strip()]
        series_list: list[pd.Series] = []

        for ticker in clean_tickers:
            df = self.client.get_prices(ticker=ticker, start=start, end=end)

            if df.empty or "Close" not in df.columns:
                continue

            returns = self._returns_by_type(df["Close"], return_type=return_type)
            returns.name = ticker
            series_list.append(returns)

        if not series_list:
            return pd.DataFrame()

        returns_df = pd.concat(series_list, axis=1).dropna()
        return returns_df

    def _annual_return_from_daily(self, daily_return: float, return_type: str) -> float:
        if return_type == "log":
            return float(np.exp(daily_return * 252) - 1.0)
        return float(daily_return * 252)

    def _daily_return_from_annual(self, annual_return: float, return_type: str) -> float:
        if return_type == "log":
            return float(np.log1p(annual_return) / 252)
        return float(annual_return / 252)

    def _portfolio_metrics(
        self,
        weights: np.ndarray,
        mean_daily: pd.Series,
        cov_daily: pd.DataFrame,
        rf_annual: float,
        return_type: str,
    ) -> dict:
        daily_return = float(np.sum(mean_daily.values * weights))
        annual_return = self._annual_return_from_daily(daily_return, return_type=return_type)

        annual_variance = float(weights.T @ (cov_daily.values * 252) @ weights)
        annual_volatility = float(np.sqrt(max(annual_variance, 0.0)))

        sharpe = 0.0
        if annual_volatility > 0:
            sharpe = float((annual_return - rf_annual) / annual_volatility)

        return {
            "return": annual_return,
            "volatility": annual_volatility,
            "sharpe": sharpe,
        }

    def _weights_payload(self, tickers: list[str], weights: np.ndarray) -> list[dict]:
        return [
            {
                "asset": tickers[i],
                "weight": float(weights[i]),
            }
            for i in range(len(tickers))
        ]

    def _portfolio_payload(
        self,
        tickers: list[str],
        weights: np.ndarray,
        metrics: dict,
    ) -> dict:
        return {
            "return": float(metrics["return"]),
            "volatility": float(metrics["volatility"]),
            "sharpe": float(metrics["sharpe"]),
            "weights": self._weights_payload(tickers, weights),
        }

    def _simulate_portfolios(
        self,
        tickers: list[str],
        mean_daily: pd.Series,
        cov_daily: pd.DataFrame,
        rf_annual: float,
        n_portfolios: int,
        return_type: str,
    ) -> tuple[list[dict], list[np.ndarray]]:
        rng = np.random.default_rng(42)

        simulated: list[dict] = []
        weights_store: list[np.ndarray] = []

        for _ in range(n_portfolios):
            weights = rng.dirichlet(np.ones(len(tickers)))

            metrics = self._portfolio_metrics(
                weights=weights,
                mean_daily=mean_daily,
                cov_daily=cov_daily,
                rf_annual=rf_annual,
                return_type=return_type,
            )

            simulated.append(
                {
                    "return": float(metrics["return"]),
                    "volatility": float(metrics["volatility"]),
                    "sharpe": float(metrics["sharpe"]),
                }
            )
            weights_store.append(weights)

        return simulated, weights_store

    def _optimize_target_variance(
        self,
        tickers: list[str],
        mean_daily: pd.Series,
        cov_daily: pd.DataFrame,
        rf_annual: float,
        return_type: str,
        target_return_annual: float,
        allow_short_selling: bool = False,
    ) -> tuple[np.ndarray, dict]:
        num_assets = len(tickers)
        target_daily = self._daily_return_from_annual(target_return_annual, return_type=return_type)
        annual_cov = cov_daily.values * 252.0

        def objective(weights: np.ndarray) -> float:
            return float(weights.T @ annual_cov @ weights)

        constraints = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},
            {"type": "eq", "fun": lambda x: float(np.sum(mean_daily.values * x) - target_daily)},
        ]
        bounds = (
            tuple((-1.0, 1.0) for _ in range(num_assets))
            if allow_short_selling
            else tuple((0.0, 1.0) for _ in range(num_assets))
        )
        init_guess = np.repeat(1.0 / num_assets, num_assets)

        result = minimize(
            objective,
            init_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-10},
        )

        if not result.success:
            raise ValueError(str(result.message))

        weights = np.asarray(result.x, dtype=float)
        metrics = self._portfolio_metrics(
            weights=weights,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
        )
        return weights, metrics

    def _build_qp_frontier_points(
        self,
        tickers: list[str],
        mean_daily: pd.Series,
        cov_daily: pd.DataFrame,
        rf_annual: float,
        return_type: str,
        allow_short_selling: bool = False,
        points: int = 40,
    ) -> list[dict]:
        min_var_weights, min_var_metrics = self._optimize_min_variance(
            tickers=tickers,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
            allow_short_selling=allow_short_selling,
        )

        max_return_weights, max_return_metrics = self._optimize_extreme_return(
            tickers=tickers,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
            allow_short_selling=allow_short_selling,
            maximize=True,
        )

        lower = float(min_var_metrics["return"])
        upper = max(float(max_return_metrics["return"]), lower)

        if np.isclose(lower, upper):
            targets = [lower]
        else:
            targets = np.linspace(lower, upper, points)

        frontier_rows: list[dict] = []
        seen: set[tuple[float, float]] = set()

        def add_row(weights: np.ndarray, metrics: dict, target: float) -> None:
            key = (round(float(metrics["volatility"]), 8), round(float(metrics["return"]), 8))
            if key in seen:
                return
            seen.add(key)
            frontier_rows.append(
                {
                    "volatility": float(metrics["volatility"]),
                    "return": float(metrics["return"]),
                    "sharpe": float(metrics["sharpe"]),
                    "target_return": float(target),
                    "weights": self._weights_payload(tickers, weights),
                }
            )

        add_row(min_var_weights, min_var_metrics, lower)

        for target in targets:
            try:
                weights, metrics = self._optimize_target_variance(
                    tickers=tickers,
                    mean_daily=mean_daily,
                    cov_daily=cov_daily,
                    rf_annual=rf_annual,
                    return_type=return_type,
                    target_return_annual=float(target),
                    allow_short_selling=allow_short_selling,
                )
            except Exception:
                continue

            add_row(weights, metrics, float(target))

        add_row(max_return_weights, max_return_metrics, upper)

        return self._upper_efficient_frontier(frontier_rows)

    def _upper_efficient_frontier(self, rows: list[dict]) -> list[dict]:
        if not rows:
            return []

        by_risk: dict[float, dict] = {}
        for row in rows:
            risk_key = round(float(row["volatility"]), 10)
            previous = by_risk.get(risk_key)
            if previous is None or float(row["return"]) > float(previous["return"]):
                by_risk[risk_key] = row

        ordered = sorted(by_risk.values(), key=lambda item: (float(item["volatility"]), float(item["return"])))
        efficient: list[dict] = []
        best_return = -np.inf
        ret_values = [float(item["return"]) for item in ordered]
        tolerance = max(1e-10, (max(ret_values) - min(ret_values)) * 1e-6) if ret_values else 1e-10

        for row in ordered:
            row_return = float(row["return"])
            if row_return >= best_return - tolerance:
                efficient.append(row)
                best_return = max(best_return, row_return)

        return efficient

    def _optimize_extreme_return(
        self,
        tickers: list[str],
        mean_daily: pd.Series,
        cov_daily: pd.DataFrame,
        rf_annual: float,
        return_type: str,
        allow_short_selling: bool = False,
        maximize: bool = True,
    ) -> tuple[np.ndarray, dict]:
        num_assets = len(tickers)

        def objective(weights: np.ndarray) -> float:
            expected_daily = float(np.sum(mean_daily.values * weights))
            return -expected_daily if maximize else expected_daily

        constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]
        bounds = tuple((-1.0, 1.0) for _ in range(num_assets)) if allow_short_selling else tuple((0.0, 1.0) for _ in range(num_assets))
        init_guess = np.repeat(1.0 / num_assets, num_assets)

        result = minimize(
            objective,
            init_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-10},
        )

        if not result.success:
            raise ValueError(f"No fue posible calcular el portafolio de retorno extremo: {result.message}")

        weights = np.asarray(result.x, dtype=float)
        metrics = self._portfolio_metrics(
            weights=weights,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
        )
        return weights, metrics

    def _optimize_min_variance(
        self,
        tickers: list[str],
        mean_daily: pd.Series,
        cov_daily: pd.DataFrame,
        rf_annual: float,
        return_type: str,
        allow_short_selling: bool = False,
    ) -> tuple[np.ndarray, dict]:
        num_assets = len(tickers)
        annual_cov = cov_daily.values * 252.0

        def objective(weights: np.ndarray) -> float:
            return float(weights.T @ annual_cov @ weights)

        constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]
        bounds = tuple((-1.0, 1.0) for _ in range(num_assets)) if allow_short_selling else tuple((0.0, 1.0) for _ in range(num_assets))
        init_guess = np.repeat(1.0 / num_assets, num_assets)

        result = minimize(
            objective,
            init_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-12},
        )

        if not result.success:
            raise ValueError(f"No fue posible calcular el portafolio de mínima varianza: {result.message}")

        weights = np.asarray(result.x, dtype=float)
        metrics = self._portfolio_metrics(
            weights=weights,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
        )

        return weights, metrics

    def _optimize_max_sharpe(
        self,
        tickers: list[str],
        mean_daily: pd.Series,
        cov_daily: pd.DataFrame,
        rf_annual: float,
        return_type: str,
        allow_short_selling: bool = False,
    ) -> tuple[np.ndarray, dict]:
        num_assets = len(tickers)

        def objective(weights: np.ndarray) -> float:
            metrics = self._portfolio_metrics(
                weights=weights,
                mean_daily=mean_daily,
                cov_daily=cov_daily,
                rf_annual=rf_annual,
                return_type=return_type,
            )
            return -float(metrics["sharpe"])

        constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]
        bounds = tuple((-1.0, 1.0) for _ in range(num_assets)) if allow_short_selling else tuple((0.0, 1.0) for _ in range(num_assets))
        init_guess = np.repeat(1.0 / num_assets, num_assets)

        result = minimize(
            objective,
            init_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        if not result.success:
            raise ValueError(f"No fue posible calcular el portafolio de máximo Sharpe: {result.message}")

        weights = np.asarray(result.x, dtype=float)
        metrics = self._portfolio_metrics(
            weights=weights,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
        )

        return weights, metrics

    def _select_target_return_portfolio(
        self,
        target_return_annual: float | None,
        tickers: list[str],
        mean_daily: pd.Series,
        cov_daily: pd.DataFrame,
        rf_annual: float,
        return_type: str,
        allow_short_selling: bool,
    ) -> dict | None:
        if target_return_annual is None:
            return None

        try:
            selected_weights, selected_metrics = self._optimize_target_variance(
                tickers=tickers,
                mean_daily=mean_daily,
                cov_daily=cov_daily,
                rf_annual=rf_annual,
                return_type=return_type,
                target_return_annual=target_return_annual,
                allow_short_selling=allow_short_selling,
            )
        except Exception:
            return None

        return {
            "target_return_annual": float(target_return_annual),
            "achieved_return_annual": float(selected_metrics["return"]),
            "volatility_annual": float(selected_metrics["volatility"]),
            "weights": self._weights_payload(tickers, selected_weights),
        }

    def _select_profile_portfolio(
        self,
        risk_profile: str | None,
        tickers: list[str],
        min_var_weights: np.ndarray,
        min_var_metrics: dict,
        max_sharpe_weights: np.ndarray,
        max_sharpe_metrics: dict,
        simulated: list[dict],
        weights_store: list[np.ndarray],
    ) -> dict | None:
        if risk_profile is None:
            return None

        profile = risk_profile.strip().lower()

        if profile == "minimo_riesgo":
            return {
                "profile": profile,
                **self._portfolio_payload(tickers, min_var_weights, min_var_metrics),
            }

        if profile in {"maxima_utilidad", "arriesgado"}:
            return {
                "profile": profile,
                **self._portfolio_payload(tickers, max_sharpe_weights, max_sharpe_metrics),
            }

        if profile == "conservador" and simulated and weights_store:
            df = pd.DataFrame(simulated).sort_values("volatility").reset_index()
            idx = int(df.iloc[0]["index"])
            row = simulated[idx]
            weights = weights_store[idx]

            return {
                "profile": profile,
                "return": float(row["return"]),
                "volatility": float(row["volatility"]),
                "sharpe": float(row["sharpe"]),
                "weights": self._weights_payload(tickers, weights),
            }

        return None

    def _resolve_perri_horizon(self, start: str, end: str) -> str:
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)
        days = max(int((end_date - start_date).days), 1)

        candidates = {
            "1y": 365,
            "3y": 365 * 3,
            "5y": 365 * 5,
        }

        return min(candidates, key=lambda key: abs(candidates[key] - days))

    def _load_latest_perri_payload(self) -> dict | None:
        project_root = Path(__file__).resolve().parents[3]
        path = project_root / "backend" / "data" / "perri_latest_optimization.json"

        if not path.exists():
            return None

        try:
            with path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, json.JSONDecodeError):
            return None

        result = payload.get("result") if isinstance(payload, dict) else None
        return result if isinstance(result, dict) else None

    def _select_max_return_from_simulations(
        self,
        tickers: list[str],
        simulated: list[dict],
        weights_store: list[np.ndarray],
    ) -> dict | None:
        if not simulated or not weights_store:
            return None

        best_idx = None
        best_return = -np.inf

        for idx, row in enumerate(simulated):
            if idx >= len(weights_store):
                continue

            annual_return = row.get("return")
            volatility = row.get("volatility")
            sharpe = row.get("sharpe")

            if annual_return is None or volatility is None or sharpe is None:
                continue

            if not np.isfinite(float(annual_return)):
                continue

            if float(annual_return) > best_return:
                best_return = float(annual_return)
                best_idx = idx

        if best_idx is None:
            return None

        row = simulated[best_idx]

        return {
            "return": float(row["return"]),
            "volatility": float(row["volatility"]),
            "sharpe": float(row["sharpe"]),
            "weights": self._weights_payload(tickers, weights_store[best_idx]),
        }

    def _build_perri_comparison(
        self,
        portfolio_size: int,
        start: str,
        end: str,
        min_variance_payload: dict,
        max_sharpe_payload: dict,
        max_return_payload: dict | None,
    ) -> dict:
        horizon = self._resolve_perri_horizon(start=start, end=end)

        if portfolio_size not in {5, 10, 15}:
            return {
                "enabled": False,
                "portfolio_size": int(portfolio_size),
                "horizon": horizon,
                "message": "La comparación Perri solo está disponible para portafolios exactos de 5, 10 o 15 activos.",
                "comparisons": [],
            }

        perri_result = self._load_latest_perri_payload()

        if perri_result is None:
            return {
                "enabled": False,
                "portfolio_size": int(portfolio_size),
                "horizon": horizon,
                "message": "No fue posible cargar backend/data/perri_latest_optimization.json.",
                "comparisons": [],
            }

        horizon_payload = perri_result.get("horizons", {}).get(horizon)
        size_payload = None

        if isinstance(horizon_payload, dict):
            size_payload = horizon_payload.get("portfolio_sizes", {}).get(str(portfolio_size))

        if not isinstance(size_payload, dict):
            return {
                "enabled": False,
                "portfolio_size": int(portfolio_size),
                "horizon": horizon,
                "message": "No existe umbral Perri para el horizonte y tamaño solicitados.",
                "comparisons": [],
            }

        user_payload_by_objective = {
            "min_risk": min_variance_payload,
            "max_sharpe": max_sharpe_payload,
            "max_return": max_return_payload,
        }

        comparisons = []

        for objective, user_payload in user_payload_by_objective.items():
            perri_payload = size_payload.get(objective)

            if not isinstance(perri_payload, dict) or not isinstance(user_payload, dict):
                continue

            perri_return = perri_payload.get("expected_return_annual")
            perri_volatility = perri_payload.get("volatility_annual")
            perri_sharpe = perri_payload.get("sharpe")

            user_return = float(user_payload["return"])
            user_volatility = float(user_payload["volatility"])
            user_sharpe = float(user_payload["sharpe"])

            return_gap = None if perri_return is None else user_return - float(perri_return)
            volatility_gap = None if perri_volatility is None else user_volatility - float(perri_volatility)
            sharpe_gap = None if perri_sharpe is None else user_sharpe - float(perri_sharpe)

            if objective == "min_risk":
                verdict = (
                    "El portafolio del usuario tiene menor o igual volatilidad que Perri."
                    if volatility_gap is not None and volatility_gap <= 0
                    else "Perri mantiene menor volatilidad institucional para este tamaño y horizonte."
                )
            elif objective == "max_sharpe":
                verdict = (
                    "El portafolio del usuario iguala o supera el Sharpe de Perri."
                    if sharpe_gap is not None and sharpe_gap >= 0
                    else "Perri mantiene mejor relación riesgo-retorno por Sharpe."
                )
            else:
                verdict = (
                    "El portafolio del usuario iguala o supera el retorno de Perri."
                    if return_gap is not None and return_gap >= 0
                    else "Perri mantiene mayor retorno esperado para este tamaño y horizonte."
                )

            comparisons.append(
                {
                    "objective": objective,
                    "perri_return": None if perri_return is None else float(perri_return),
                    "perri_volatility": None if perri_volatility is None else float(perri_volatility),
                    "perri_sharpe": None if perri_sharpe is None else float(perri_sharpe),
                    "user_return": user_return,
                    "user_volatility": user_volatility,
                    "user_sharpe": user_sharpe,
                    "return_gap": return_gap,
                    "volatility_gap": volatility_gap,
                    "sharpe_gap": sharpe_gap,
                    "verdict": verdict,
                }
            )

        return {
            "enabled": True,
            "portfolio_size": int(portfolio_size),
            "horizon": horizon,
            "message": "Comparación contra umbrales institucionales Perri generada correctamente.",
            "comparisons": comparisons,
        }

    def _select_top_portfolios(
        self,
        tickers: list[str],
        simulated: list[dict],
        weights_store: list[np.ndarray],
        top_n: int = 5,
    ) -> list[dict]:
        if not simulated or not weights_store:
            return []

        ranked_rows = []

        for idx, row in enumerate(simulated):
            if idx >= len(weights_store):
                continue

            sharpe = row.get("sharpe")
            annual_return = row.get("return")
            volatility = row.get("volatility")

            if sharpe is None or annual_return is None or volatility is None:
                continue

            if not np.isfinite(float(sharpe)):
                continue

            ranked_rows.append(
                {
                    "rank": len(ranked_rows) + 1,
                    "return": float(annual_return),
                    "volatility": float(volatility),
                    "sharpe": float(sharpe),
                    "weights": self._weights_payload(tickers, weights_store[idx]),
                }
            )

        ranked_rows = sorted(
            ranked_rows,
            key=lambda item: item["sharpe"],
            reverse=True,
        )

        top = ranked_rows[:top_n]

        for i, item in enumerate(top, start=1):
            item["rank"] = i

        return top

    def _build_short_selling_comparison(
        self,
        tickers: list[str],
        mean_daily: pd.Series,
        cov_daily: pd.DataFrame,
        rf_annual: float,
        return_type: str,
    ) -> dict:
        try:
            restricted_min_w, restricted_min_m = self._optimize_min_variance(
                tickers=tickers,
                mean_daily=mean_daily,
                cov_daily=cov_daily,
                rf_annual=rf_annual,
                return_type=return_type,
                allow_short_selling=False,
            )
            restricted_sharpe_w, restricted_sharpe_m = self._optimize_max_sharpe(
                tickers=tickers,
                mean_daily=mean_daily,
                cov_daily=cov_daily,
                rf_annual=rf_annual,
                return_type=return_type,
                allow_short_selling=False,
            )
            short_min_w, short_min_m = self._optimize_min_variance(
                tickers=tickers,
                mean_daily=mean_daily,
                cov_daily=cov_daily,
                rf_annual=rf_annual,
                return_type=return_type,
                allow_short_selling=True,
            )
            short_sharpe_w, short_sharpe_m = self._optimize_max_sharpe(
                tickers=tickers,
                mean_daily=mean_daily,
                cov_daily=cov_daily,
                rf_annual=rf_annual,
                return_type=return_type,
                allow_short_selling=True,
            )
        except Exception as exc:
            return {
                "available": False,
                "message": f"No fue posible comparar restricciones de no negatividad: {exc}",
            }

        def _negative_assets(weights: np.ndarray) -> list[str]:
            return [tickers[i] for i, weight in enumerate(weights) if float(weight) < -1e-6]

        def _zero_assets(weights: np.ndarray) -> list[str]:
            return [tickers[i] for i, weight in enumerate(weights) if abs(float(weight)) <= 1e-4]

        restricted_frontier = self._build_qp_frontier_points(
            tickers=tickers,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
            allow_short_selling=False,
        )
        short_frontier = self._build_qp_frontier_points(
            tickers=tickers,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
            allow_short_selling=True,
        )
        variance_cost = float(restricted_min_m["volatility"] ** 2 - short_min_m["volatility"] ** 2)
        sharpe_cost = float(short_sharpe_m["sharpe"] - restricted_sharpe_m["sharpe"])

        return {
            "available": True,
            "methodology": (
                "Cada frontera se resuelve como QP: minimizar w' Sigma w sujeto a retorno objetivo, "
                "suma de pesos igual a 1 y, en la version B, w_i >= 0."
            ),
            "restricted": {
                "description": "Sin short selling: pesos entre 0% y 100%.",
                "restriction": "w_i >= 0",
                "frontier": restricted_frontier,
                "min_variance": self._portfolio_payload(tickers, restricted_min_w, restricted_min_m),
                "max_sharpe": self._portfolio_payload(tickers, restricted_sharpe_w, restricted_sharpe_m),
                "zero_weight_assets": sorted(set(_zero_assets(restricted_min_w) + _zero_assets(restricted_sharpe_w))),
            },
            "with_short_selling": {
                "description": "Con short selling metodologico: pesos entre -100% y 100%, suma total 100%.",
                "restriction": "w_i in R con bounds numericos [-100%, 100%]",
                "frontier": short_frontier,
                "min_variance": self._portfolio_payload(tickers, short_min_w, short_min_m),
                "max_sharpe": self._portfolio_payload(tickers, short_sharpe_w, short_sharpe_m),
                "negative_weight_assets": sorted(set(_negative_assets(short_min_w) + _negative_assets(short_sharpe_w))),
            },
            "cost_of_no_short_constraint": {
                "variance_cost_min_variance": variance_cost,
                "sharpe_opportunity_cost": sharpe_cost,
                "return_gap_max_sharpe": float(short_sharpe_m["return"] - restricted_sharpe_m["return"]),
                "volatility_gap_min_variance": float(restricted_min_m["volatility"] - short_min_m["volatility"]),
            },
            "interpretation": (
                "Si el caso con short selling mejora Sharpe o reduce volatilidad, la restriccion de no negatividad "
                "esta limitando la frontera. Si no mejora de forma relevante, el portafolio long-only es suficiente "
                "y mas defendible para un inversionista tradicional."
            ),
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
        allow_short_selling: bool = False,
    ) -> dict:
        returns_df = self._build_returns_matrix(
            tickers=tickers,
            start=start,
            end=end,
            return_type=return_type,
        )

        if returns_df.empty:
            raise ValueError("No fue posible construir la matriz de rendimientos del portafolio.")

        if len(returns_df.columns) != len(tickers):
            raise ValueError("No fue posible obtener datos válidos para todos los tickers enviados.")

        if len(returns_df) < self.client.settings.min_obs_portfolio:
            raise ValueError(
                f"Se requieren al menos {self.client.settings.min_obs_portfolio} observaciones "
                "para optimización de portafolio."
            )

        effective_tickers = list(returns_df.columns)
        mean_daily = returns_df.mean()
        cov_daily = returns_df.cov()
        corr_matrix = returns_df.corr().round(6).to_dict()

        simulated, weights_store = self._simulate_portfolios(
            tickers=effective_tickers,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            n_portfolios=n_portfolios,
            return_type=return_type,
        )

        frontier = self._build_qp_frontier_points(
            tickers=effective_tickers,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
            allow_short_selling=allow_short_selling,
        )

        min_var_weights, min_var_metrics = self._optimize_min_variance(
            tickers=effective_tickers,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
            allow_short_selling=allow_short_selling,
        )

        max_sharpe_weights, max_sharpe_metrics = self._optimize_max_sharpe(
            tickers=effective_tickers,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
            allow_short_selling=allow_short_selling,
        )

        target_portfolio = self._select_target_return_portfolio(
            target_return_annual=target_return_annual,
            tickers=effective_tickers,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
            allow_short_selling=allow_short_selling,
        )

        profile_portfolio = self._select_profile_portfolio(
            risk_profile=risk_profile,
            tickers=effective_tickers,
            min_var_weights=min_var_weights,
            min_var_metrics=min_var_metrics,
            max_sharpe_weights=max_sharpe_weights,
            max_sharpe_metrics=max_sharpe_metrics,
            simulated=simulated,
            weights_store=weights_store,
        )

        min_variance_payload = self._portfolio_payload(
            effective_tickers,
            min_var_weights,
            min_var_metrics,
        )

        max_sharpe_payload = self._portfolio_payload(
            effective_tickers,
            max_sharpe_weights,
            max_sharpe_metrics,
        )

        max_return_payload = self._select_max_return_from_simulations(
            tickers=effective_tickers,
            simulated=simulated,
            weights_store=weights_store,
        )

        return {
            "tickers": effective_tickers,
            "start": start,
            "end": end,
            "rf_annual": float(rf_annual),
            "frontier": frontier,
            "simulated_portfolios": simulated,
            "correlation_matrix": corr_matrix,
            "optimization_method": "SLSQP QP: min w' Sigma w sujeto a mu'w = target, sum(w)=1 y bounds de no negatividad/short selling.",
            "frontier_method": "qp_target_return_grid",
            "simulation_count": int(n_portfolios),
            "formulation": {
                "objective": "minimize w.T @ Sigma @ w",
                "constraints": [
                    "mu.T @ w == target_return",
                    "sum(w) == 1",
                    "w_i >= 0 cuando allow_short_selling=False",
                ],
            },
            "observations": int(len(returns_df)),
            "n_assets": int(len(effective_tickers)),
            "min_variance": min_variance_payload,
            "max_sharpe": max_sharpe_payload,
            "top_portfolios": self._select_top_portfolios(
                tickers=effective_tickers,
                simulated=simulated,
                weights_store=weights_store,
                top_n=5,
            ),
            "target_return_portfolio": target_portfolio,
            "suggested_profile_portfolio": profile_portfolio,
            "perri_comparison": self._build_perri_comparison(
                portfolio_size=len(effective_tickers),
                start=start,
                end=end,
                min_variance_payload=min_variance_payload,
                max_sharpe_payload=max_sharpe_payload,
                max_return_payload=max_return_payload,
            ),
            "allow_short_selling": bool(allow_short_selling),
            "short_selling_comparison": self._build_short_selling_comparison(
                tickers=effective_tickers,
                mean_daily=mean_daily,
                cov_daily=cov_daily,
                rf_annual=rf_annual,
                return_type=return_type,
            ),
        }
