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

        # arch trabaja mejor con retornos en porcentaje
        returns = returns * 100.0
        returns.name = ticker.upper()
        return returns

    def analyze(
        self,
        ticker: str,
        start: str,
        end: str,
        return_type: str,
        mode: str,
        forecast_horizon: int,
    ) -> dict:
        returns = self._get_returns(ticker=ticker, start=start, end=end, return_type=return_type)

        if len(returns) < 100:
            raise ValueError("No hay suficientes observaciones para ajustar modelos de volatilidad.")

        model_specs = [
            ("ARCH(1)", {"mean": "Constant", "vol": "ARCH", "p": 1, "o": 0, "q": 0, "dist": "normal"}),
            ("GARCH(1,1)", {"mean": "Constant", "vol": "GARCH", "p": 1, "o": 0, "q": 1, "dist": "normal"}),
            ("EGARCH(1,1)", {"mean": "Constant", "vol": "EGARCH", "p": 1, "o": 0, "q": 1, "dist": "normal"}),
        ]

        fitted_models = []

        for name, spec in model_specs:
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

        residuals_conclusion = (
            "Se rechaza normalidad de residuos estandarizados al 5%."
            if jb_p < 0.05
            else "No se rechaza normalidad de residuos estandarizados al 5%."
        )

        cond_vol = [float(x) for x in best_res.conditional_volatility.tolist()]

        try:
            forecast_res = best_res.forecast(horizon=forecast_horizon, reindex=False)
            effective_horizon = forecast_horizon
        except Exception:
            forecast_res = best_res.forecast(horizon=1, reindex=False)
            effective_horizon = 1

        forecast_variances = forecast_res.variance.iloc[-1].values.tolist()

        forecast = [
            {
                "step": i + 1,
                "variance": float(v),
                "volatility": float(np.sqrt(v)),
            }
            for i, v in enumerate(forecast_variances)
        ]

        if mode == "general":
            summary = (
                f"Se compararon ARCH(1), GARCH(1,1) y EGARCH(1,1). "
                f"El mejor modelo por AIC fue {best_name}. "
                f"El diagnostico de residuos indica: {residuals_conclusion} "
                f"El horizonte efectivo de pronostico fue {effective_horizon}."
            )
        else:
            summary = (
                f"Best model={best_name}, "
                f"AIC={float(best_res.aic):.6f}, "
                f"BIC={float(best_res.bic):.6f}, "
                f"JB p-value residuos={float(jb_p):.6f}, "
                f"effective_horizon={effective_horizon}."
            )

        return {
            "ticker": ticker.upper(),
            "start": start,
            "end": end,
            "return_type": return_type,
            "observations": int(len(returns)),
            "candidate_models": candidate_models,
            "best_model": best_name,
            "best_model_aic": float(best_res.aic),
            "best_model_bic": float(best_res.bic),
            "residuals_jarque_bera_stat": float(jb_stat),
            "residuals_jarque_bera_p_value": float(jb_p),
            "residuals_normality_conclusion": residuals_conclusion,
            "conditional_volatility": cond_vol,
            "forecast": forecast,
            "mode": mode,
            "summary": summary,
            "effective_forecast_horizon": int(effective_horizon),
        }