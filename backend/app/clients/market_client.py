from __future__ import annotations

import pandas as pd
import yfinance as yf

from app.core.decorators import log_execution_time
from app.core.market_utils import normalize_end_date_to_available_data, validate_not_future
from app.core.assets_registry import ASSET_METADATA_BY_TICKER
from app.core.settings import Settings


class MarketClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _download_prices(self, ticker: str, start: str, end: str) -> pd.DataFrame:
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

    def _convert_ohlc_to_usd(self, prices: pd.DataFrame, ticker: str, start: str, end: str) -> pd.DataFrame:
        if prices.empty:
            return prices

        meta = ASSET_METADATA_BY_TICKER.get(ticker.upper(), {})
        currency = str(meta.get("currency", "USD")).upper()
        fx_ticker = meta.get("fx_to_usd")
        price_scale = float(meta.get("price_scale", 1.0))

        out = prices.copy()

        price_cols = [col for col in ["Open", "High", "Low", "Close", "Adj Close"] if col in out.columns]

        # Primero corrige escala, por ejemplo pence a libras en BP.L
        if price_scale != 1.0:
            for col in price_cols:
                out[col] = pd.to_numeric(out[col], errors="coerce") * price_scale

        # Si ya está en USD, no convierte
        if currency == "USD" or not fx_ticker:
            out["Currency"] = currency
            out["BaseCurrency"] = "USD"
            out["FxTicker"] = None
            out["FxRateToUSD"] = 1.0
            return out

        fx = self._download_prices(fx_ticker, start=start, end=end)
        if fx.empty or "Close" not in fx.columns:
            raise ValueError(f"No fue posible obtener la divisa histórica {fx_ticker} para convertir {ticker} a USD.")

        fx_close = pd.to_numeric(fx["Close"], errors="coerce").rename("FxRateToUSD").dropna()

        joined = out.join(fx_close, how="left")
        joined["FxRateToUSD"] = joined["FxRateToUSD"].ffill().bfill()

        if joined["FxRateToUSD"].isna().all():
            raise ValueError(f"No hay datos válidos de FX para convertir {ticker} a USD.")

        for col in price_cols:
            joined[col] = pd.to_numeric(joined[col], errors="coerce") * joined["FxRateToUSD"]

        joined["Currency"] = currency
        joined["BaseCurrency"] = "USD"
        joined["FxTicker"] = fx_ticker

        return joined

    @log_execution_time
    def get_prices(self, ticker: str, start: str, end: str, convert_to_usd: bool = True) -> pd.DataFrame:
        validate_not_future(start=start, end=end)

        out = self._download_prices(ticker=ticker, start=start, end=end)

        if out.empty:
            return pd.DataFrame()

        if convert_to_usd:
            out = self._convert_ohlc_to_usd(
                prices=out,
                ticker=ticker,
                start=start,
                end=end,
            )

        return out.copy()