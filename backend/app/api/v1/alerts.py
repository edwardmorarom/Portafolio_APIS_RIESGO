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
    service: AlertsService = Depends(get_alerts_service),
) -> AlertsResponse:
    try:
        result = service.get_alerts(ticker=ticker, start=start, end=end)
        return AlertsResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc