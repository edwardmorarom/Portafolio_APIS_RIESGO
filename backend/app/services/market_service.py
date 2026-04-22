from __future__ import annotations

import numpy as np
import pandas as pd

from app.clients.market_client import MarketClient


class MarketService:
    def __init__(self, client: MarketClient) -> None:
        self.client = client

    def get_prices(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        return self.client.get_prices(ticker=ticker, start=start, end=end)

    def get_returns(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        prices = self.client.get_prices(ticker=ticker, start=start, end=end)
        if prices.empty or "Close" not in prices.columns:
            return pd.DataFrame()

        close = pd.to_numeric(prices["Close"], errors="coerce")
        close = close.replace([np.inf, -np.inf], np.nan).dropna()

        out = pd.DataFrame(index=close.index)
        out["simple_return"] = close.pct_change()
        out["log_return"] = np.log(close / close.shift(1))
        out = out.replace([np.inf, -np.inf], np.nan).dropna()

        return out