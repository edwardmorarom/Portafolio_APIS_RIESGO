from __future__ import annotations

import pandas as pd
import yfinance as yf

from app.core.decorators import log_execution_time
from app.core.market_utils import normalize_end_date_to_available_data, validate_not_future
from app.core.settings import Settings


class MarketClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @log_execution_time
    def get_prices(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        validate_not_future(start=start, end=end)

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

        out = normalize_end_date_to_available_data(out)

        keep_cols = [c for c in ["Open", "High", "Low", "Close", "Adj Close", "Volume"] if c in out.columns]
        return out[keep_cols].copy()