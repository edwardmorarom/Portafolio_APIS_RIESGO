from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.market_client import MarketClient
from app.db.models import Asset, Price


class MarketService:
    def __init__(self, client: MarketClient) -> None:
        self.client = client

    def _get_prices_from_db(
        self,
        ticker: str,
        start: str,
        end: str,
        db: Session,
    ) -> pd.DataFrame:
        ticker_clean = ticker.strip().upper()

        start_date = pd.to_datetime(start).date()
        end_date = pd.to_datetime(end).date()

        asset = db.scalar(select(Asset).where(Asset.ticker == ticker_clean))

        if asset is None:
            return pd.DataFrame()

        prices = list(
            db.scalars(
                select(Price)
                .where(Price.asset_id == asset.id)
                .where(Price.date >= start_date)
                .where(Price.date <= end_date)
                .order_by(Price.date.asc())
            )
        )

        if not prices:
            return pd.DataFrame()

        records = []

        for price in prices:
            close_usd = price.close_usd if price.close_usd is not None else price.close

            records.append(
                {
                    "Date": price.date,
                    "Open": None,
                    "High": None,
                    "Low": None,
                    "Close": close_usd,
                    "Adj Close": close_usd,
                    "Volume": None,
                    "Currency": price.original_currency,
                    "BaseCurrency": "USD",
                    "FxTicker": price.fx_ticker,
                    "FxRateToUSD": price.fx_rate_to_usd,
                }
            )

        df = pd.DataFrame(records)

        if df.empty:
            return pd.DataFrame()

        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")

        return df

    def get_prices(
        self,
        ticker: str,
        start: str,
        end: str,
        db: Session | None = None,
    ) -> pd.DataFrame:
        if db is not None:
            db_prices = self._get_prices_from_db(
                ticker=ticker,
                start=start,
                end=end,
                db=db,
            )

            if not db_prices.empty:
                return db_prices

        return self.client.get_prices(ticker=ticker, start=start, end=end)

    def get_returns(
        self,
        ticker: str,
        start: str,
        end: str,
        db: Session | None = None,
    ) -> pd.DataFrame:
        prices = self.get_prices(ticker=ticker, start=start, end=end, db=db)

        if prices.empty or "Close" not in prices.columns:
            return pd.DataFrame()

        close = pd.to_numeric(prices["Close"], errors="coerce")
        close = close.replace([np.inf, -np.inf], np.nan).dropna()

        out = pd.DataFrame(index=close.index)
        out["simple_return"] = close.pct_change()
        out["log_return"] = np.log(close / close.shift(1))
        out = out.replace([np.inf, -np.inf], np.nan).dropna()

        return out