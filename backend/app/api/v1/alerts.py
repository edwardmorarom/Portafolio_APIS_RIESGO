from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_alerts_service
from app.schemas.alerts import AlertsResponse
from app.services.alerts_service import AlertsService

router = APIRouter()


@router.get("/{ticker}", summary="Alertas tecnicas por activo", response_model=AlertsResponse)
async def get_alerts(
    ticker: str,
    start: str = Query(default="2021-01-01"),
    end: str = Query(default="2026-12-31"),
    rsi_overbought: float = Query(default=70.0, ge=50.0, le=100.0),
    rsi_oversold: float = Query(default=30.0, ge=0.0, le=50.0),
    stoch_overbought: float = Query(default=80.0, ge=50.0, le=100.0),
    stoch_oversold: float = Query(default=20.0, ge=0.0, le=50.0),
    service: AlertsService = Depends(get_alerts_service),
) -> AlertsResponse:
    try:
        result = service.get_alerts(
            ticker=ticker,
            start=start,
            end=end,
            rsi_overbought=rsi_overbought,
            rsi_oversold=rsi_oversold,
            stoch_overbought=stoch_overbought,
            stoch_oversold=stoch_oversold,
        )
        return AlertsResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc