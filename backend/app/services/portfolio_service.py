from __future__ import annotations

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

    def _build_frontier_points(self, simulated: list[dict]) -> list[dict]:
        if not simulated:
            return []

        df = pd.DataFrame(simulated)
        df = df.replace([np.inf, -np.inf], np.nan).dropna()

        if df.empty:
            return []

        df = df.sort_values(["volatility", "return"]).reset_index(drop=True)

        frontier_rows: list[dict] = []
        best_return_so_far = -np.inf

        for _, row in df.iterrows():
            current_return = float(row["return"])

            if current_return > best_return_so_far:
                frontier_rows.append(
                    {
                        "volatility": float(row["volatility"]),
                        "return": current_return,
                        "sharpe": float(row["sharpe"]),
                    }
                )
                best_return_so_far = current_return

        if len(frontier_rows) > 300:
            indexes = np.linspace(0, len(frontier_rows) - 1, 300).astype(int)
            frontier_rows = [frontier_rows[i] for i in indexes]

        return frontier_rows

    def _optimize_min_variance(
        self,
        tickers: list[str],
        mean_daily: pd.Series,
        cov_daily: pd.DataFrame,
        rf_annual: float,
        return_type: str,
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
            return float(metrics["volatility"])

        constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]
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
        simulated: list[dict],
        weights_store: list[np.ndarray],
    ) -> dict | None:
        if target_return_annual is None or not simulated or not weights_store:
            return None

        df = pd.DataFrame(simulated)
        if df.empty or "return" not in df.columns:
            return None

        idx = int((df["return"] - target_return_annual).abs().idxmin())
        selected_weights = weights_store[idx]
        selected_row = simulated[idx]

        return {
            "target_return_annual": float(target_return_annual),
            "achieved_return_annual": float(selected_row["return"]),
            "volatility_annual": float(selected_row["volatility"]),
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

        frontier = self._build_frontier_points(simulated)

        min_var_weights, min_var_metrics = self._optimize_min_variance(
            tickers=effective_tickers,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
        )

        max_sharpe_weights, max_sharpe_metrics = self._optimize_max_sharpe(
            tickers=effective_tickers,
            mean_daily=mean_daily,
            cov_daily=cov_daily,
            rf_annual=rf_annual,
            return_type=return_type,
        )

        target_portfolio = self._select_target_return_portfolio(
            target_return_annual=target_return_annual,
            tickers=effective_tickers,
            simulated=simulated,
            weights_store=weights_store,
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

        return {
            "tickers": effective_tickers,
            "start": start,
            "end": end,
            "rf_annual": float(rf_annual),
            "frontier": frontier,
            "simulated_portfolios": simulated,
            "correlation_matrix": corr_matrix,
            "observations": int(len(returns_df)),
            "n_assets": int(len(effective_tickers)),
            "min_variance": self._portfolio_payload(
                effective_tickers,
                min_var_weights,
                min_var_metrics,
            ),
            "max_sharpe": self._portfolio_payload(
                effective_tickers,
                max_sharpe_weights,
                max_sharpe_metrics,
            ),
            "top_portfolios": self._select_top_portfolios(
                tickers=effective_tickers,
                simulated=simulated,
                weights_store=weights_store,
                top_n=5,
            ),
            "target_return_portfolio": target_portfolio,
            "suggested_profile_portfolio": profile_portfolio,
        }