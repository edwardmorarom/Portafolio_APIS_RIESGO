from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from app.clients.market_client import MarketClient
from app.core.exceptions import TickerNotFoundError


class ReturnsStatsService:
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

        returns.name = ticker.upper()
        return returns

    def _normality_conclusion(self, p_value: float | None) -> str:
        if p_value is None:
            return "No fue posible concluir normalidad."
        if p_value < 0.05:
            return "Se rechaza normalidad al 5%."
        return "No se rechaza normalidad al 5%."

    def build_returns_stats(
        self,
        ticker: str,
        start: str,
        end: str,
        return_type: str,
        mode: str,
    ) -> dict:
        returns = self._get_returns(ticker=ticker, start=start, end=end, return_type=return_type)

        values = returns.values.astype(float)
        n = len(values)

        mean = float(np.mean(values))
        std = float(np.std(values, ddof=1))
        skewness = float(stats.skew(values, bias=False))
        kurtosis = float(stats.kurtosis(values, fisher=True, bias=False))
        min_return = float(np.min(values))
        max_return = float(np.max(values))

        # Shapiro-Wilk
        shapiro_stat, shapiro_p = stats.shapiro(values) if n >= 3 and n <= 5000 else (None, None)

        # Jarque-Bera
        jb_stat, jb_p = stats.jarque_bera(values)

        # Anderson-Darling
        ad_result = stats.anderson(values, dist="norm")
        ad_stat = float(ad_result.statistic)
        ad_crit = [float(x) for x in ad_result.critical_values]
        ad_sig = [float(x) for x in ad_result.significance_level]
        ad_conclusion = (
            "Hay evidencia contra normalidad al 5%."
            if ad_stat > ad_crit[2]
            else "No hay evidencia suficiente contra normalidad al 5%."
        )

        # Histogram
        counts, bin_edges = np.histogram(values, bins="auto")
        histogram = []
        for i in range(len(counts)):
            histogram.append(
                {
                    "left": float(bin_edges[i]),
                    "right": float(bin_edges[i + 1]),
                    "count": int(counts[i]),
                }
            )

        # QQ plot
        theoretical, sample = stats.probplot(values, dist="norm", fit=False)
        qq_plot = [
            {"theoretical": float(t), "sample": float(s)}
            for t, s in zip(theoretical, sample)
        ]

        # Boxplot
        q1, median, q3 = np.percentile(values, [25, 50, 75])
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        non_outliers = values[(values >= lower_fence) & (values <= upper_fence)]
        outliers = values[(values < lower_fence) | (values > upper_fence)]

        boxplot = {
            "min": float(np.min(non_outliers)) if len(non_outliers) else float(np.min(values)),
            "q1": float(q1),
            "median": float(median),
            "q3": float(q3),
            "max": float(np.max(non_outliers)) if len(non_outliers) else float(np.max(values)),
            "outliers": [float(x) for x in outliers.tolist()],
        }

        if mode == "general":
            summary = (
                f"Se analizaron {n} rendimientos {return_type}. "
                f"La media fue {mean:.4f}, la volatilidad {std:.4f} "
                f"y las pruebas sugieren "
                f"{'comportamiento cercano a normalidad' if jb_p >= 0.05 else 'desviaciones frente a normalidad'}."
            )
        else:
            summary = (
                f"n={n}, mean={mean:.6f}, std={std:.6f}, skewness={skewness:.6f}, kurtosis={kurtosis:.6f}, "
                f"Shapiro p={shapiro_p if shapiro_p is not None else 'NA'}, "
                f"JB p={float(jb_p):.6f}, AD stat={ad_stat:.6f}."
            )

        return {
            "ticker": ticker.upper(),
            "start": start,
            "end": end,
            "return_type": return_type,
            "observations": n,
            "mean": mean,
            "std": std,
            "skewness": skewness,
            "kurtosis": kurtosis,
            "min_return": min_return,
            "max_return": max_return,
            "shapiro_wilk": {
                "statistic": None if shapiro_stat is None else float(shapiro_stat),
                "p_value": None if shapiro_p is None else float(shapiro_p),
                "conclusion": self._normality_conclusion(None if shapiro_p is None else float(shapiro_p)),
            },
            "jarque_bera": {
                "statistic": float(jb_stat),
                "p_value": float(jb_p),
                "conclusion": self._normality_conclusion(float(jb_p)),
            },
            "anderson_darling": {
                "statistic": ad_stat,
                "critical_values": ad_crit,
                "significance_levels": ad_sig,
                "conclusion": ad_conclusion,
            },
            "histogram": histogram,
            "qq_plot": qq_plot,
            "boxplot": boxplot,
            "mode": mode,
            "summary": summary,
        }