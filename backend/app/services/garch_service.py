from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from arch import arch_model

from app.clients.market_client import MarketClient
from app.core.exceptions import TickerNotFoundError


class GarchService:
    def __init__(self, client: MarketClient) -> None:
        self.client = client

    def _get_returns(self, ticker: str, start: str, end: str, return_type: str) -> pd.Series:
        df = self.client.get_prices(ticker=ticker, start=start, end=end)
        if df.empty or "Close" not in df.columns:
            raise TickerNotFoundError(ticker=ticker)

        close = pd.to_numeric(df["Close"], errors="coerce").dropna()

        if return_type == "log":
            returns = np.log(close / close.shift(1)).dropna()
        else:
            returns = close.pct_change().dropna()

        if returns.empty:
            raise TickerNotFoundError(ticker=ticker)

        returns = returns * 100.0
        returns.name = ticker.upper()
        return returns

    @staticmethod
    def _safe_float_list(values) -> list[float]:
        out: list[float] = []
        if values is None:
            return out

        for value in values:
            try:
                f_value = float(value)
                if np.isfinite(f_value):
                    out.append(f_value)
            except Exception:
                continue
        return out

    @staticmethod
    def _normalize_distribution(distribution: str) -> str:
        value = str(distribution or "normal").strip().lower()
        if value in {"student", "student-t", "t-student", "t_student"}:
            value = "t"
        return "t" if value == "t" else "normal"

    @staticmethod
    def _distribution_label(distribution: str) -> str:
        return "t-Student" if distribution == "t" else "Normal"

    @staticmethod
    def _calculate_ewma_volatility(returns: pd.Series, ewma_lambda: float) -> list[float]:
        clean = pd.to_numeric(returns, errors="coerce").dropna()
        if clean.empty:
            return []

        lambda_value = min(max(float(ewma_lambda), 0.70), 0.99)
        initial_variance = float(clean.var(ddof=1)) if len(clean) > 1 else float(clean.iloc[0] ** 2)
        variance = max(initial_variance, 0.0)
        out: list[float] = []

        for value in clean:
            variance = (lambda_value * variance) + ((1.0 - lambda_value) * float(value) ** 2)
            out.append(float(np.sqrt(max(variance, 0.0))))

        return out

    @staticmethod
    def _calculate_rolling_volatility(returns: pd.Series, window: int = 20) -> list[float]:
        """
        Volatilidad muestral rodante para comparar contra EWMA.

        La serie de retornos ya viene escalada en porcentaje, por lo que la salida
        queda en la misma escala que ARCH/GARCH/EGARCH y EWMA.
        """
        clean = pd.to_numeric(returns, errors="coerce").dropna()

        if len(clean) < window:
            return []

        rolling = clean.rolling(window=window).std(ddof=1).dropna()
        return [
            float(value)
            for value in rolling.tolist()
            if np.isfinite(float(value))
        ]

    @staticmethod
    def _arch_lm_test(std_resid: pd.Series, lags: int = 5) -> dict[str, float | int | str]:
        clean = pd.to_numeric(std_resid, errors="coerce").dropna()
        squared = clean.pow(2)
        effective_lags = min(max(int(lags), 1), max(len(squared) // 5, 1), 10)

        if len(squared) <= effective_lags + 5:
            return {
                "lags": int(effective_lags),
                "stat": 0.0,
                "p_value": 1.0,
                "conclusion": "No hay observaciones suficientes para ARCH-LM.",
            }

        y = squared.iloc[effective_lags:].to_numpy(dtype=float)
        x_columns = [
            squared.shift(lag).iloc[effective_lags:].to_numpy(dtype=float)
            for lag in range(1, effective_lags + 1)
        ]
        x = np.column_stack([np.ones(len(y)), *x_columns])

        try:
            beta, *_ = np.linalg.lstsq(x, y, rcond=None)
            fitted = x @ beta
            total_ss = float(np.sum((y - y.mean()) ** 2))
            residual_ss = float(np.sum((y - fitted) ** 2))
            r_squared = 0.0 if total_ss <= 0 else max(0.0, min(1.0, 1.0 - residual_ss / total_ss))
            lm_stat = float(len(y) * r_squared)
            p_value = float(stats.chi2.sf(lm_stat, effective_lags))
        except Exception:
            lm_stat = 0.0
            p_value = 1.0

        conclusion = (
            "Se detecta heterocedasticidad ARCH remanente al 5%."
            if p_value < 0.05
            else "No se detecta heterocedasticidad ARCH remanente al 5%."
        )
        return {
            "lags": int(effective_lags),
            "stat": float(lm_stat),
            "p_value": float(p_value),
            "conclusion": conclusion,
        }

    @staticmethod
    def _forecast_variances(res, horizon: int) -> list[float]:
        for kwargs in (
            {"horizon": horizon, "reindex": False},
            {"horizon": horizon, "reindex": False, "method": "simulation", "simulations": 500},
            {"horizon": horizon, "reindex": False, "method": "bootstrap", "simulations": 500},
        ):
            try:
                forecast_res = res.forecast(**kwargs)
                values = forecast_res.variance.iloc[-1].values.tolist()
                out = [
                    float(value)
                    for value in values
                    if np.isfinite(float(value)) and float(value) >= 0
                ]
                if out:
                    return out[:horizon]
            except Exception:
                continue

        try:
            last_variance = float(pd.Series(res.conditional_volatility).dropna().iloc[-1] ** 2)
        except Exception:
            last_variance = 0.0
        return [last_variance for _ in range(horizon)]

    def analyze(
        self,
        ticker: str,
        start: str,
        end: str,
        return_type: str,
        mode: str,
        forecast_horizon: int,
        distribution: str = "normal",
        ewma_lambda: float = 0.94,
    ) -> dict:
        distribution = self._normalize_distribution(distribution)
        dist_label = self._distribution_label(distribution)
        ewma_lambda = min(max(float(ewma_lambda), 0.70), 0.99)

        returns = self._get_returns(
            ticker=ticker,
            start=start,
            end=end,
            return_type=return_type,
        )

        if len(returns) < 100:
            raise ValueError("No hay suficientes observaciones para ajustar modelos de volatilidad.")

        ewma_volatility = self._calculate_ewma_volatility(returns, ewma_lambda=ewma_lambda)
        rolling_volatility_window = 20
        rolling_volatility = self._calculate_rolling_volatility(
            returns=returns,
            window=rolling_volatility_window,
        )
        ewma_latest = ewma_volatility[-1] if ewma_volatility else None
        ewma_forecast = [
            {
                "step": int(step),
                "variance": float(ewma_latest**2) if ewma_latest is not None else 0.0,
                "volatility": float(ewma_latest) if ewma_latest is not None else 0.0,
            }
            for step in range(1, forecast_horizon + 1)
        ]

        model_specs = [
            ("ARCH(1)", {"mean": "Constant", "vol": "ARCH", "p": 1, "o": 0, "q": 0, "dist": distribution}),
            ("GARCH(1,1)", {"mean": "Constant", "vol": "GARCH", "p": 1, "o": 0, "q": 1, "dist": distribution}),
            ("EGARCH(1,1)", {"mean": "Constant", "vol": "EGARCH", "p": 1, "o": 0, "q": 1, "dist": distribution}),
        ]

        fitted_models: list[tuple[str, object]] = []

        for name, spec in model_specs:
            try:
                model = arch_model(
                    returns,
                    mean=spec["mean"],
                    vol=spec["vol"],
                    p=spec["p"],
                    o=spec["o"],
                    q=spec["q"],
                    dist=spec["dist"],
                    rescale=False,
                )
                res = model.fit(disp="off")
                fitted_models.append((name, res))
            except Exception:
                continue

        if not fitted_models:
            raise ValueError("No fue posible ajustar modelos ARCH/GARCH/EGARCH con la muestra disponible.")

        candidate_models = [
            {
                "model_name": name,
                "log_likelihood": float(res.loglikelihood),
                "aic": float(res.aic),
                "bic": float(res.bic),
            }
            for name, res in fitted_models
        ]

        best_name, best_res = min(fitted_models, key=lambda x: x[1].aic)

        std_resid = pd.Series(best_res.std_resid).dropna()
        jb_stat, jb_p = stats.jarque_bera(std_resid)
        arch_lm = self._arch_lm_test(std_resid, lags=5)

        residuals_conclusion = (
            "Se rechaza normalidad de residuos estandarizados al 5%."
            if jb_p < 0.05
            else "No se rechaza normalidad de residuos estandarizados al 5%."
        )

        conditional_volatility_by_model: dict[str, list[float]] = {}
        forecast_by_model: dict[str, list[float]] = {}

        effective_horizon = forecast_horizon

        for name, res in fitted_models:
            try:
                cond_vol_values = self._safe_float_list(res.conditional_volatility.tolist())
            except Exception:
                cond_vol_values = []

            conditional_volatility_by_model[name] = cond_vol_values

            model_forecast_variances = self._forecast_variances(res, horizon=forecast_horizon)

            forecast_by_model[name] = [
                float(np.sqrt(v)) for v in model_forecast_variances if np.isfinite(v) and v >= 0
            ]

        cond_vol = conditional_volatility_by_model.get(best_name, [])

        best_forecast_volatility = forecast_by_model.get(best_name, [])

        forecast: list[dict[str, float | int]] = []
        for i, volatility in enumerate(best_forecast_volatility, start=1):
            variance = float(volatility) ** 2
            forecast.append(
                {
                    "step": i,
                    "variance": float(variance),
                    "volatility": float(volatility),
                }
            )

        effective_forecast_horizon = len(forecast) if forecast else int(effective_horizon)

        if mode == "general":
            summary = (
                f"Se compararon ARCH(1), GARCH(1,1) y EGARCH(1,1) con errores {dist_label}. "
                f"El mejor modelo por AIC fue {best_name}. "
                f"El diagnostico de residuos indica: {residuals_conclusion} "
                f"El horizonte efectivo de pronostico fue {effective_forecast_horizon}."
            )
        else:
            summary = (
                f"Best model={best_name}, "
                f"distribution={dist_label}, "
                f"AIC={float(best_res.aic):.6f}, "
                f"BIC={float(best_res.bic):.6f}, "
                f"JB p-value residuos={float(jb_p):.6f}, "
                f"ARCH-LM p-value={float(arch_lm['p_value']):.6f}, "
                f"effective_horizon={effective_forecast_horizon}."
            )

        return {
            "ticker": ticker.upper(),
            "start": start,
            "end": end,
            "return_type": return_type,
            "observations": int(len(returns)),
            "distribution": distribution,
            "distribution_label": dist_label,
            "ewma_lambda": float(ewma_lambda),
            "ewma_volatility": ewma_volatility,
            "ewma_latest_volatility": None if ewma_latest is None else float(ewma_latest),
            "ewma_forecast": ewma_forecast,
            "rolling_volatility_window": int(rolling_volatility_window),
            "rolling_volatility": rolling_volatility,
            "candidate_models": candidate_models,
            "best_model": best_name,
            "best_model_aic": float(best_res.aic),
            "best_model_bic": float(best_res.bic),
            "residuals_jarque_bera_stat": float(jb_stat),
            "residuals_jarque_bera_p_value": float(jb_p),
            "residuals_normality_conclusion": residuals_conclusion,
            "arch_lm_lags": int(arch_lm["lags"]),
            "arch_lm_stat": float(arch_lm["stat"]),
            "arch_lm_p_value": float(arch_lm["p_value"]),
            "arch_lm_conclusion": str(arch_lm["conclusion"]),
            "conditional_volatility": cond_vol,
            "conditional_volatility_by_model": conditional_volatility_by_model,
            "forecast": forecast,
            "forecast_by_model": forecast_by_model,
            "mode": mode,
            "summary": summary,
            "effective_forecast_horizon": int(effective_forecast_horizon),
        }
