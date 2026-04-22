from __future__ import annotations

import numpy as np
import pandas as pd

from app.clients.market_client import MarketClient
from app.core.exceptions import TickerNotFoundError


class AlertsService:
    def __init__(self, client: MarketClient) -> None:
        self.client = client

    def _load_data(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        df = self.client.get_prices(ticker=ticker, start=start, end=end)
        if df.empty or "Close" not in df.columns:
            raise TickerNotFoundError(ticker=ticker)
        return df.copy()

    def get_alerts(self, ticker: str, start: str, end: str) -> dict:
        df = self._load_data(ticker=ticker, start=start, end=end)

        close = pd.to_numeric(df["Close"], errors="coerce")
        high = pd.to_numeric(df["High"], errors="coerce") if "High" in df.columns else close
        low = pd.to_numeric(df["Low"], errors="coerce") if "Low" in df.columns else close

        out = pd.DataFrame(index=df.index)
        out["close"] = close

        # SMA / EMA
        out["sma_20"] = close.rolling(20).mean()
        out["ema_20"] = close.ewm(span=20, adjust=False).mean()

        # RSI
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

        # Bollinger
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std(ddof=1)
        out["bb_up"] = bb_mid + 2.0 * bb_std
        out["bb_low"] = bb_mid - 2.0 * bb_std

        # Stochastic
        low_n = low.rolling(14).min()
        high_n = high.rolling(14).max()
        denom = (high_n - low_n).replace(0, np.nan)
        out["stoch_k"] = 100 * (close - low_n) / denom
        out["stoch_d"] = out["stoch_k"].rolling(3).mean()

        out = out.replace([np.inf, -np.inf], np.nan).dropna()
        if out.empty or len(out) < 2:
            raise TickerNotFoundError(ticker=ticker)

        last = out.iloc[-1]
        prev = out.iloc[-2]

        alerts = []

        # RSI
        if last["rsi_14"] >= 70:
            alerts.append({
                "indicator": "RSI",
                "signal": "sobrecompra",
                "severity": "media",
                "general_message": "El activo podria estar en zona de sobrecompra.",
                "statistical_message": f"RSI={last['rsi_14']:.2f}, por encima de 70."
            })
        elif last["rsi_14"] <= 30:
            alerts.append({
                "indicator": "RSI",
                "signal": "sobreventa",
                "severity": "media",
                "general_message": "El activo podria estar en zona de sobreventa.",
                "statistical_message": f"RSI={last['rsi_14']:.2f}, por debajo de 30."
            })

        # MACD cross
        if prev["macd"] <= prev["macd_signal"] and last["macd"] > last["macd_signal"]:
            alerts.append({
                "indicator": "MACD",
                "signal": "cruce_alcista",
                "severity": "alta",
                "general_message": "Se detecta una posible señal alcista por cruce MACD.",
                "statistical_message": "MACD cruzo por encima de la linea de señal."
            })
        elif prev["macd"] >= prev["macd_signal"] and last["macd"] < last["macd_signal"]:
            alerts.append({
                "indicator": "MACD",
                "signal": "cruce_bajista",
                "severity": "alta",
                "general_message": "Se detecta una posible señal bajista por cruce MACD.",
                "statistical_message": "MACD cruzo por debajo de la linea de señal."
            })

        # Bollinger
        if last["close"] >= last["bb_up"]:
            alerts.append({
                "indicator": "Bollinger",
                "signal": "toque_banda_superior",
                "severity": "media",
                "general_message": "El precio toco o supero la banda superior de Bollinger.",
                "statistical_message": "Close >= banda superior de Bollinger."
            })
        elif last["close"] <= last["bb_low"]:
            alerts.append({
                "indicator": "Bollinger",
                "signal": "toque_banda_inferior",
                "severity": "media",
                "general_message": "El precio toco o perforo la banda inferior de Bollinger.",
                "statistical_message": "Close <= banda inferior de Bollinger."
            })

        # Moving average cross
        if prev["sma_20"] <= prev["ema_20"] and last["sma_20"] > last["ema_20"]:
            alerts.append({
                "indicator": "MovingAverages",
                "signal": "cruce_alcista_medias",
                "severity": "media",
                "general_message": "Se observa un cruce alcista entre medias moviles.",
                "statistical_message": "SMA20 cruzo por encima de EMA20."
            })
        elif prev["sma_20"] >= prev["ema_20"] and last["sma_20"] < last["ema_20"]:
            alerts.append({
                "indicator": "MovingAverages",
                "signal": "cruce_bajista_medias",
                "severity": "media",
                "general_message": "Se observa un cruce bajista entre medias moviles.",
                "statistical_message": "SMA20 cruzo por debajo de EMA20."
            })

        # Stochastic
        if prev["stoch_k"] <= prev["stoch_d"] and last["stoch_k"] > last["stoch_d"] and last["stoch_k"] < 20:
            alerts.append({
                "indicator": "Stochastic",
                "signal": "cruce_alcista_sobreventa",
                "severity": "alta",
                "general_message": "El estocastico sugiere rebote desde zona de sobreventa.",
                "statistical_message": "%K cruzo por encima de %D en zona menor a 20."
            })
        elif prev["stoch_k"] >= prev["stoch_d"] and last["stoch_k"] < last["stoch_d"] and last["stoch_k"] > 80:
            alerts.append({
                "indicator": "Stochastic",
                "signal": "cruce_bajista_sobrecompra",
                "severity": "alta",
                "general_message": "El estocastico sugiere debilidad desde zona de sobrecompra.",
                "statistical_message": "%K cruzo por debajo de %D en zona mayor a 80."
            })

        return {
            "ticker": ticker.upper(),
            "start": start,
            "end": end,
            "alerts": alerts,
            "total_alerts": len(alerts),
        }