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

    def get_alerts(
        self,
        ticker: str,
        start: str,
        end: str,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0,
        stoch_overbought: float = 80.0,
        stoch_oversold: float = 20.0,
        sma_short_window: int = 20,
        sma_long_window: int = 50,
    ) -> dict:
        if sma_short_window >= sma_long_window:
            raise ValueError("sma_short_window debe ser menor que sma_long_window")

        df = self._load_data(ticker=ticker, start=start, end=end)

        close = pd.to_numeric(df["Close"], errors="coerce")
        high = pd.to_numeric(df["High"], errors="coerce") if "High" in df.columns else close
        low = pd.to_numeric(df["Low"], errors="coerce") if "Low" in df.columns else close

        out = pd.DataFrame(index=df.index)
        out["close"] = close

        out["sma_short"] = close.rolling(sma_short_window).mean()
        out["sma_long"] = close.rolling(sma_long_window).mean()
        out["ema_20"] = close.ewm(span=20, adjust=False).mean()

        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        out["rsi_14"] = 100 - (100 / (1 + rs))

        ema_fast = close.ewm(span=12, adjust=False).mean()
        ema_slow = close.ewm(span=26, adjust=False).mean()
        out["macd"] = ema_fast - ema_slow
        out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()

        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std(ddof=1)
        out["bb_up"] = bb_mid + 2.0 * bb_std
        out["bb_low"] = bb_mid - 2.0 * bb_std

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

        items: list[dict] = []
        total_alerts = 0

        # RSI
        rsi_value = float(last["rsi_14"])
        rsi_status = "normal"
        rsi_signal = "sin_senal"
        rsi_severity = "baja"
        rsi_general = "El RSI está en zona neutral."
        rsi_stat = f"RSI={rsi_value:.2f}."

        if rsi_value >= rsi_overbought:
            rsi_status = "alert"
            rsi_signal = "sobrecompra"
            rsi_severity = "media"
            rsi_general = "El activo podría estar en zona de sobrecompra."
            rsi_stat = f"RSI={rsi_value:.2f}, por encima de {rsi_overbought:.2f}."
            total_alerts += 1
        elif rsi_value <= rsi_oversold:
            rsi_status = "alert"
            rsi_signal = "sobreventa"
            rsi_severity = "media"
            rsi_general = "El activo podría estar en zona de sobreventa."
            rsi_stat = f"RSI={rsi_value:.2f}, por debajo de {rsi_oversold:.2f}."
            total_alerts += 1
        elif rsi_value >= rsi_overbought - 5 or rsi_value <= rsi_oversold + 5:
            rsi_status = "watch"
            rsi_signal = "cercano_umbral"
            rsi_severity = "baja"
            rsi_general = "El RSI está cerca de una zona extrema."
            rsi_stat = f"RSI={rsi_value:.2f}, cercano a umbrales."

        items.append({
            "indicator": "RSI",
            "rule": "rsi_extreme_zone",
            "status": rsi_status,
            "signal": rsi_signal,
            "severity": rsi_severity,
            "value": rsi_value,
            "threshold_low": rsi_oversold,
            "threshold_high": rsi_overbought,
            "general_message": rsi_general,
            "statistical_message": rsi_stat,
        })

        # MACD
        macd_value = float(last["macd"] - last["macd_signal"])
        macd_status = "normal"
        macd_signal_name = "sin_senal"
        macd_severity = "baja"
        macd_general = "No se detecta cruce reciente del MACD."
        macd_stat = f"MACD-line minus signal={macd_value:.4f}."

        if prev["macd"] <= prev["macd_signal"] and last["macd"] > last["macd_signal"]:
            macd_status = "alert"
            macd_signal_name = "cruce_alcista"
            macd_severity = "alta"
            macd_general = "Se detecta una posible señal alcista por cruce MACD."
            macd_stat = "MACD cruzó por encima de la línea de señal."
            total_alerts += 1
        elif prev["macd"] >= prev["macd_signal"] and last["macd"] < last["macd_signal"]:
            macd_status = "alert"
            macd_signal_name = "cruce_bajista"
            macd_severity = "alta"
            macd_general = "Se detecta una posible señal bajista por cruce MACD."
            macd_stat = "MACD cruzó por debajo de la línea de señal."
            total_alerts += 1
        elif abs(macd_value) < 0.05:
            macd_status = "watch"
            macd_signal_name = "cercano_cruce"
            macd_general = "El MACD está cerca de un posible cruce."
            macd_stat = f"Diferencia MACD-señal={macd_value:.4f}, cercana a cero."

        items.append({
            "indicator": "MACD",
            "rule": "macd_signal_cross",
            "status": macd_status,
            "signal": macd_signal_name,
            "severity": macd_severity,
            "value": macd_value,
            "threshold_low": None,
            "threshold_high": None,
            "general_message": macd_general,
            "statistical_message": macd_stat,
        })

        # Bollinger
        close_value = float(last["close"])
        bb_status = "normal"
        bb_signal = "sin_senal"
        bb_severity = "baja"
        bb_general = "El precio está dentro de las bandas de Bollinger."
        bb_stat = f"Close={close_value:.4f}, BB_low={float(last['bb_low']):.4f}, BB_up={float(last['bb_up']):.4f}."

        if last["close"] >= last["bb_up"]:
            bb_status = "alert"
            bb_signal = "toque_banda_superior"
            bb_severity = "media"
            bb_general = "El precio tocó o superó la banda superior de Bollinger."
            bb_stat = "Close >= banda superior de Bollinger."
            total_alerts += 1
        elif last["close"] <= last["bb_low"]:
            bb_status = "alert"
            bb_signal = "toque_banda_inferior"
            bb_severity = "media"
            bb_general = "El precio tocó o perforó la banda inferior de Bollinger."
            bb_stat = "Close <= banda inferior de Bollinger."
            total_alerts += 1

        items.append({
            "indicator": "Bollinger",
            "rule": "bollinger_band_touch",
            "status": bb_status,
            "signal": bb_signal,
            "severity": bb_severity,
            "value": close_value,
            "threshold_low": float(last["bb_low"]),
            "threshold_high": float(last["bb_up"]),
            "general_message": bb_general,
            "statistical_message": bb_stat,
        })

        # Moving averages
        ma_diff = float(last["sma_short"] - last["sma_long"])
        ma_status = "normal"
        ma_signal = "sin_senal"
        ma_severity = "baja"
        ma_general = "No se detecta cruce reciente entre medias móviles."
        ma_stat = f"SMA{sma_short_window}-SMA{sma_long_window}={ma_diff:.4f}."

        if prev["sma_short"] <= prev["sma_long"] and last["sma_short"] > last["sma_long"]:
            ma_status = "alert"
            ma_signal = "golden_cross"
            ma_severity = "media"
            ma_general = "Se observa un cruce alcista entre medias móviles."
            ma_stat = f"SMA{sma_short_window} cruzo por encima de SMA{sma_long_window}."
            total_alerts += 1
        elif prev["sma_short"] >= prev["sma_long"] and last["sma_short"] < last["sma_long"]:
            ma_status = "alert"
            ma_signal = "death_cross"
            ma_severity = "media"
            ma_general = "Se observa un cruce bajista entre medias móviles."
            ma_stat = f"SMA{sma_short_window} cruzo por debajo de SMA{sma_long_window}."
            total_alerts += 1
        elif abs(ma_diff) < 0.1:
            ma_status = "watch"
            ma_signal = "cercano_cruce_medias"
            ma_general = "Las medias están muy próximas entre sí."
            ma_stat = f"SMA{sma_short_window}-SMA{sma_long_window}={ma_diff:.4f}, cercana a cero."

        items.append({
            "indicator": "MovingAverages",
            "rule": "sma_golden_death_cross",
            "status": ma_status,
            "signal": ma_signal,
            "severity": ma_severity,
            "value": ma_diff,
            "threshold_low": None,
            "threshold_high": None,
            "general_message": ma_general,
            "statistical_message": ma_stat,
        })

        # Stochastic
        stoch_value = float(last["stoch_k"])
        stoch_status = "normal"
        stoch_signal = "sin_senal"
        stoch_severity = "baja"
        stoch_general = "El estocástico está en zona neutral."
        stoch_stat = f"%K={float(last['stoch_k']):.2f}, %D={float(last['stoch_d']):.2f}."

        if prev["stoch_k"] <= prev["stoch_d"] and last["stoch_k"] > last["stoch_d"] and last["stoch_k"] < stoch_oversold:
            stoch_status = "alert"
            stoch_signal = "cruce_alcista_sobreventa"
            stoch_severity = "alta"
            stoch_general = "El estocástico sugiere rebote desde zona de sobreventa."
            stoch_stat = f"%K cruzó por encima de %D en zona menor a {stoch_oversold:.2f}."
            total_alerts += 1
        elif prev["stoch_k"] >= prev["stoch_d"] and last["stoch_k"] < last["stoch_d"] and last["stoch_k"] > stoch_overbought:
            stoch_status = "alert"
            stoch_signal = "cruce_bajista_sobrecompra"
            stoch_severity = "alta"
            stoch_general = "El estocástico sugiere debilidad desde zona de sobrecompra."
            stoch_stat = f"%K cruzó por debajo de %D en zona mayor a {stoch_overbought:.2f}."
            total_alerts += 1
        elif stoch_value >= stoch_overbought - 5 or stoch_value <= stoch_oversold + 5:
            stoch_status = "watch"
            stoch_signal = "cercano_umbral_estocastico"
            stoch_general = "El estocástico está cerca de una zona extrema."
            stoch_stat = f"%K={stoch_value:.2f}, cercano a umbrales."

        items.append({
            "indicator": "Stochastic",
            "rule": "stochastic_kd_extreme_cross",
            "status": stoch_status,
            "signal": stoch_signal,
            "severity": stoch_severity,
            "value": stoch_value,
            "threshold_low": stoch_oversold,
            "threshold_high": stoch_overbought,
            "general_message": stoch_general,
            "statistical_message": stoch_stat,
        })

        return {
            "ticker": ticker.upper(),
            "start": start,
            "end": end,
            "alerts": items,
            "total_alerts": total_alerts,
        }
