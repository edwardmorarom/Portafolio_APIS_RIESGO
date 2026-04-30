from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_market_service
from app.schemas.market import PricePoint, PricesResponse, ReturnPoint, ReturnsResponse
from app.services.market_service import MarketService

router = APIRouter()

@router.get("/prices/{ticker}", summary="Precios históricos por ticker", response_model=PricesResponse)
async def get_prices(
    ticker: str,
    start: str = Query(default="2021-01-01"),
    end: str = Query(default="2026-12-31"),
    service: MarketService = Depends(get_market_service),
) -> PricesResponse:
    df = service.get_prices(ticker=ticker, start=start, end=end)

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No se encontraron precios para {ticker}")

    records: list[PricePoint] = []
    for idx, row in df.iterrows():
        records.append(
            PricePoint(
                date=pd.to_datetime(idx).strftime("%Y-%m-%d"),
                open=float(row["Open"]) if "Open" in row and pd.notna(row["Open"]) else None,
                high=float(row["High"]) if "High" in row and pd.notna(row["High"]) else None,
                low=float(row["Low"]) if "Low" in row and pd.notna(row["Low"]) else None,
                close=float(row["Close"]) if "Close" in row and pd.notna(row["Close"]) else None,
                adj_close=float(row["Adj Close"]) if "Adj Close" in row and pd.notna(row["Adj Close"]) else None,
                volume=float(row["Volume"]) if "Volume" in row and pd.notna(row["Volume"]) else None,
                currency=str(row["Currency"]) if "Currency" in row and pd.notna(row["Currency"]) else None,
                base_currency=str(row["BaseCurrency"]) if "BaseCurrency" in row and pd.notna(row["BaseCurrency"]) else None,
                fx_ticker=str(row["FxTicker"]) if "FxTicker" in row and pd.notna(row["FxTicker"]) else None,
                fx_rate_to_usd=float(row["FxRateToUSD"]) if "FxRateToUSD" in row and pd.notna(row["FxRateToUSD"]) else None,
            )
        )

    return PricesResponse(
        ticker=ticker.upper(),
        start=start,
        end=end,
        message="Precios descargados correctamente",
        data=records,
    )


@router.get("/returns/{ticker}", summary="Rendimientos por ticker", response_model=ReturnsResponse)
async def get_returns(
    ticker: str,
    start: str = Query(default="2021-01-01"),
    end: str = Query(default="2026-12-31"),
    service: MarketService = Depends(get_market_service),
) -> ReturnsResponse:
    df = service.get_returns(ticker=ticker, start=start, end=end)

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No se encontraron rendimientos para {ticker}")

    records: list[ReturnPoint] = []
    for idx, row in df.iterrows():
        records.append(
            ReturnPoint(
                date=pd.to_datetime(idx).strftime("%Y-%m-%d"),
                simple_return=float(row["simple_return"]) if pd.notna(row["simple_return"]) else None,
                log_return=float(row["log_return"]) if pd.notna(row["log_return"]) else None,
            )
        )

    return ReturnsResponse(
        ticker=ticker.upper(),
        start=start,
        end=end,
        message="Rendimientos simples y logarítmicos calculados correctamente",
        data=records,
    )