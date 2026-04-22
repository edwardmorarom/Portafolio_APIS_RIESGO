from __future__ import annotations

import numpy as np
import pandas as pd

from app.clients.market_client import MarketClient


class TechnicalService:
    def __init__(self, client: MarketClient) -> None:
        self.client = client

    def get_indicators(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        df = self.client.get_prices(ticker=ticker, start=start, end=end)
        if df.empty or "Close" not in df.columns:
            return pd.DataFrame()

        out = df.copy()

        close = pd.to_numeric(out["Close"], errors="coerce")
        high = pd.to_numeric(out["High"], errors="coerce") if "High" in out.columns else close
        low = pd.to_numeric(out["Low"], errors="coerce") if "Low" in out.columns else close

        # SMA / EMA
        out["sma_20"] = close.rolling(20).mean()
        out["ema_20"] = close.ewm(span=20, adjust=False).mean()

        # RSI 14
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        out["rsi_14"] = 100 - (100 / (1 + rs))

        # MACD
        ema_fast = close.ewm(span=12, adjust=False).mean()
        ema_slow = close.ewm(span=26, adjust=False).mean()
        out["macd"] = ema_fast - ema_slow
        out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()
        out["macd_hist"] = out["macd"] - out["macd_signal"]

        # Bollinger
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std(ddof=1)
        out["bb_mid"] = bb_mid
        out["bb_up"] = bb_mid + 2.0 * bb_std
        out["bb_low"] = bb_mid - 2.0 * bb_std

        # Stochastic
        low_n = low.rolling(14).min()
        high_n = high.rolling(14).max()
        denom = (high_n - low_n).replace(0, np.nan)
        out["stoch_k"] = 100 * (close - low_n) / denom
        out["stoch_d"] = out["stoch_k"].rolling(3).mean()

        return out.replace([np.inf, -np.inf], np.nan).dropna().copy()