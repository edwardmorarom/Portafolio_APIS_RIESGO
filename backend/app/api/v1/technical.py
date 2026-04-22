from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_technical_service
from app.schemas.technical import TechnicalPoint, TechnicalResponse
from app.services.technical_service import TechnicalService

router = APIRouter()


@router.get("/indicators/{ticker}", summary="Indicadores técnicos por ticker", response_model=TechnicalResponse)
async def get_indicators(
    ticker: str,
    start: str = Query(default="2021-01-01"),
    end: str = Query(default="2026-12-31"),
    service: TechnicalService = Depends(get_technical_service),
) -> TechnicalResponse:
    df = service.get_indicators(ticker=ticker, start=start, end=end)

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No se encontraron indicadores para {ticker}")

    records: list[TechnicalPoint] = []
    for idx, row in df.iterrows():
        records.append(
            TechnicalPoint(
                date=pd.to_datetime(idx).strftime("%Y-%m-%d"),
                close=float(row["Close"]) if pd.notna(row["Close"]) else None,
                sma_20=float(row["sma_20"]) if pd.notna(row["sma_20"]) else None,
                ema_20=float(row["ema_20"]) if pd.notna(row["ema_20"]) else None,
                rsi_14=float(row["rsi_14"]) if pd.notna(row["rsi_14"]) else None,
                macd=float(row["macd"]) if pd.notna(row["macd"]) else None,
                macd_signal=float(row["macd_signal"]) if pd.notna(row["macd_signal"]) else None,
                macd_hist=float(row["macd_hist"]) if pd.notna(row["macd_hist"]) else None,
                bb_mid=float(row["bb_mid"]) if pd.notna(row["bb_mid"]) else None,
                bb_up=float(row["bb_up"]) if pd.notna(row["bb_up"]) else None,
                bb_low=float(row["bb_low"]) if pd.notna(row["bb_low"]) else None,
                stoch_k=float(row["stoch_k"]) if pd.notna(row["stoch_k"]) else None,
                stoch_d=float(row["stoch_d"]) if pd.notna(row["stoch_d"]) else None,
            )
        )

    return TechnicalResponse(
        ticker=ticker.upper(),
        start=start,
        end=end,
        message="Indicadores técnicos calculados correctamente",
        data=records,
    )