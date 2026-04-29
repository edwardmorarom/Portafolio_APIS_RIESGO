from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2, norm, t

from app.clients.market_client import MarketClient


class RiskService:
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

    def _portfolio_returns(self, returns_df: pd.DataFrame, weights: list[float]) -> pd.Series:
        w = np.asarray(weights, dtype=float)
        port = returns_df @ w
        port.name = "portfolio_return"
        return port

    @staticmethod
    def _normalize_distribution(distribution: str) -> str:
        value = str(distribution or "normal").strip().lower()
        if value in {"student", "student-t", "t-student", "t_student"}:
            return "t"
        return "t" if value == "t" else "normal"

    @staticmethod
    def _distribution_label(distribution: str) -> str:
        return "t-Student" if distribution == "t" else "Normal"

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
            "distribution": "Empírica histórica",
        }

    def _monte_carlo_var_cvar(
        self,
        returns_df: pd.DataFrame,
        weights: list[float],
        alpha: float,
        n_sim: int,
        distribution: str,
        df_t: int = 5,
    ) -> tuple[dict, np.ndarray]:
        w = np.asarray(weights, dtype=float)
        mu = returns_df.mean().values
        cov = returns_df.cov().values

        rng = np.random.default_rng(42)

        if distribution == "t":
            # Simulación multivariada t-Student con covarianza aproximada igual a la histórica.
            # Para df>2, Cov(t) = df/(df-2) * scale_matrix.
            scale_cov = cov * ((df_t - 2) / df_t) if df_t > 2 else cov
            z = rng.multivariate_normal(np.zeros(len(mu)), scale_cov, size=n_sim)
            u = rng.chisquare(df_t, size=n_sim)
            sims = mu + z / np.sqrt(u[:, None] / df_t)
        else:
            sims = rng.multivariate_normal(mu, cov, size=n_sim)

        port_sim = sims @ w

        q = 1 - alpha
        cutoff = float(np.quantile(port_sim, q))
        tail = port_sim[port_sim <= cutoff]

        var_daily = max(0.0, -cutoff)
        cvar_daily = max(var_daily, float(-tail.mean()) if len(tail) > 0 else var_daily)

        result = {
            "var_daily": float(var_daily),
            "cvar_daily": float(cvar_daily),
            "var_annualized": float(var_daily * np.sqrt(252)),
            "cvar_annualized": float(cvar_daily * np.sqrt(252)),
            "distribution": self._distribution_label(distribution),
        }
        return result, port_sim

    def _parametric_var_cvar(
        self,
        portfolio_returns: pd.Series,
        alpha: float,
        distribution: str,
        df_t: int = 5,
    ) -> dict:
        mu = float(portfolio_returns.mean())
        sigma = float(portfolio_returns.std(ddof=1))
        tail_prob = 1.0 - alpha

        if np.isclose(sigma, 0.0):
            var_daily = max(0.0, -mu)
            cvar_daily = var_daily
        elif distribution == "t":
            # Paramétrico t-Student. Se ajusta la escala para que la desviación histórica
            # sea comparable con la varianza de una t con df_t grados de libertad.
            q = float(t.ppf(tail_prob, df=df_t))
            scale = sigma / np.sqrt(df_t / (df_t - 2)) if df_t > 2 else sigma

            var_return = mu + scale * q

            cvar_return = mu - scale * (
                (t.pdf(q, df_t) * (df_t + q**2))
                / ((df_t - 1) * tail_prob)
            )

            var_daily = max(0.0, -float(var_return))
            cvar_daily = max(var_daily, -float(cvar_return))
        else:
            z = float(norm.ppf(tail_prob))
            pdf_z = float(norm.pdf(z))

            var_return = mu + sigma * z
            cvar_return = mu - sigma * (pdf_z / tail_prob)

            var_daily = max(0.0, -float(var_return))
            cvar_daily = max(var_daily, -float(cvar_return))

        return {
            "var_daily": float(var_daily),
            "cvar_daily": float(cvar_daily),
            "var_annualized": float(var_daily * np.sqrt(252)),
            "cvar_annualized": float(cvar_daily * np.sqrt(252)),
            "distribution": self._distribution_label(distribution),
        }

    def _kupiec_test(self, portfolio_returns: pd.Series, alpha: float, var_daily: float) -> dict:
        n = int(len(portfolio_returns))
        if n == 0:
            return {
                "violations": 0,
                "observed_rate": 0.0,
                "expected_rate": 1 - alpha,
                "p_value": 1.0,
                "conclusion": "No hay observaciones suficientes para aplicar Kupiec.",
            }

        violations = int((portfolio_returns < -var_daily).sum())
        observed_rate = violations / n
        expected_rate = 1 - alpha

        if violations == 0 or violations == n:
            p_value = 0.0 if violations != int(round(n * expected_rate)) else 1.0
        else:
            pi_hat = violations / n

            log_l_null = ((n - violations) * np.log(1 - expected_rate)) + (violations * np.log(expected_rate))
            log_l_alt = ((n - violations) * np.log(1 - pi_hat)) + (violations * np.log(pi_hat))
            lr_uc = -2.0 * (log_l_null - log_l_alt)
            p_value = float(1.0 - chi2.cdf(lr_uc, df=1))

        conclusion = (
            "No se rechaza la calibración del VaR con el test de Kupiec al 5%."
            if p_value >= 0.05
            else "Se rechaza la calibración del VaR con el test de Kupiec al 5%."
        )

        return {
            "violations": violations,
            "observed_rate": float(observed_rate),
            "expected_rate": float(expected_rate),
            "p_value": float(p_value),
            "conclusion": conclusion,
        }

    def calculate_var(
        self,
        tickers: list[str],
        weights: list[float],
        start: str,
        end: str,
        alpha: float,
        n_sim: int,
        return_type: str,
        distribution: str = "normal",
    ) -> dict:
        distribution = self._normalize_distribution(distribution)

        returns_df = self._build_returns_matrix(
            tickers=tickers,
            start=start,
            end=end,
            return_type=return_type,
        )

        if returns_df.empty:
            raise ValueError("No fue posible construir la matriz de rendimientos.")

        if len(returns_df.columns) != len(tickers):
            raise ValueError("No fue posible obtener datos válidos para todos los tickers enviados.")

        portfolio_returns = self._portfolio_returns(returns_df, weights)

        if len(returns_df) < self.client.settings.min_obs_var:
            raise ValueError(f"Se requieren al menos {self.client.settings.min_obs_var} observaciones para VaR.")

        historical = self._historical_var_cvar(portfolio_returns, alpha=alpha)
        monte_carlo, simulated_returns = self._monte_carlo_var_cvar(
            returns_df=returns_df,
            weights=weights,
            alpha=alpha,
            n_sim=n_sim,
            distribution=distribution,
        )
        parametric = self._parametric_var_cvar(
            portfolio_returns=portfolio_returns,
            alpha=alpha,
            distribution=distribution,
        )

        kupiec_test = self._kupiec_test(
            portfolio_returns=portfolio_returns,
            alpha=alpha,
            var_daily=historical["var_daily"],
        )

        return {
            "tickers": [t.upper() for t in tickers],
            "weights": weights,
            "alpha": alpha,
            "start": start,
            "end": end,
            "distribution": distribution,
            "distribution_label": self._distribution_label(distribution),
            "parametric": parametric,
            "historical": historical,
            "monte_carlo": monte_carlo,
            "portfolio_returns": [float(x) for x in portfolio_returns.tolist()],
            "simulated_returns": [float(x) for x in simulated_returns.tolist()],
            "kupiec_test": kupiec_test,
        }
