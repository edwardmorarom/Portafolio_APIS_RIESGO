from __future__ import annotations

from datetime import datetime

import pandas as pd
import yfinance as yf

from app.core.settings import Settings


class MacroClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _get_last_close(self, ticker: str) -> float | None:
        df = yf.download(
            ticker,
            period="1mo",
            interval="1d",
            auto_adjust=False,
            progress=False,
            actions=False,
            threads=False,
            timeout=self.settings.macro_timeout_seconds,
        )

        if df is None or df.empty or "Close" not in df.columns:
            return None

        out = df.copy()
        if isinstance(out.columns, pd.MultiIndex):
            level0 = out.columns.get_level_values(0)
            out.columns = level0

        close = pd.to_numeric(out["Close"], errors="coerce").dropna()
        if close.empty:
            return None

        return float(close.iloc[-1])

    def get_macro_snapshot(self, base_currency: str) -> dict:
        base_currency = base_currency.upper()

        if base_currency == "USD":
            rf_ticker = self.settings.rf_ticker_usd
            note = "Rf basada en USD usando yfinance."
        elif base_currency == "EUR":
            rf_ticker = self.settings.rf_ticker_eur
            note = "Rf basada en EUR usando yfinance."
        else:
            rf_ticker = self.settings.rf_ticker_cop_proxy
            note = "COP usa proxy de Rf en USD por restricciones actuales de fuente/tokens."

        rf_value = self._get_last_close(rf_ticker)
        usdcop_value = self._get_last_close("USDCOP=X")

        return {
            "base_currency": base_currency,
            "benchmark_ticker": self.settings.global_benchmark,
            "rf_ticker": rf_ticker,
            "risk_free_rate_pct": rf_value,
            "inflation_yoy": None,
            "cop_per_usd": usdcop_value,
            "usdcop_market": usdcop_value,
            "source": "yfinance",
            "note": note,
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }