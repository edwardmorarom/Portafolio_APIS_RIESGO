from __future__ import annotations

import pandas as pd
import yfinance as yf

from app.core.settings import Settings


class MarketClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_prices(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        df = yf.download(
            ticker,
            start=start,
            end=end,
            auto_adjust=False,
            progress=False,
            actions=False,
            threads=False,
            timeout=self.settings.yahoo_timeout_seconds,
        )

        if df is None or df.empty:
            return pd.DataFrame()

        out = df.copy()

        if isinstance(out.columns, pd.MultiIndex):
            level0 = out.columns.get_level_values(0)
            expected = {"Open", "High", "Low", "Close", "Adj Close", "Volume"}
            if set(level0).intersection(expected):
                out.columns = level0
            else:
                out.columns = [str(col[0]) for col in out.columns]

        out.index = pd.to_datetime(out.index)
        out = out.sort_index()
        out = out[~out.index.duplicated(keep="last")]

        keep_cols = [c for c in ["Open", "High", "Low", "Close", "Adj Close", "Volume"] if c in out.columns]
        return out[keep_cols].copy()