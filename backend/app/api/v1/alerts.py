from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_alerts_service, get_db
from app.db.models import SignalLog
from app.schemas.alerts import AlertsRequestParams, AlertsResponse
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
    sma_short_window: int = Query(default=20, ge=2, le=120),
    sma_long_window: int = Query(default=50, ge=5, le=260),
    service: AlertsService = Depends(get_alerts_service),
    db: Session = Depends(get_db),
) -> AlertsResponse:
    try:
        params = AlertsRequestParams(
            ticker=ticker,
            start=start,
            end=end,
            rsi_overbought=rsi_overbought,
            rsi_oversold=rsi_oversold,
            stoch_overbought=stoch_overbought,
            stoch_oversold=stoch_oversold,
            sma_short_window=sma_short_window,
            sma_long_window=sma_long_window,
        )
        result = service.get_alerts(
            ticker=params.ticker,
            start=params.start,
            end=params.end,
            rsi_overbought=params.rsi_overbought,
            rsi_oversold=params.rsi_oversold,
            stoch_overbought=params.stoch_overbought,
            stoch_oversold=params.stoch_oversold,
            sma_short_window=params.sma_short_window,
            sma_long_window=params.sma_long_window,
        )
        response = AlertsResponse(**result)

        for item in response.alerts:
            if item.status != "alert":
                continue
            db.add(
                SignalLog(
                    ticker=response.ticker,
                    rule=item.rule,
                    value=item.value,
                    signal=item.signal,
                    status=item.status,
                    severity=item.severity,
                    payload=item.model_dump(),
                )
            )
        db.commit()

        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
