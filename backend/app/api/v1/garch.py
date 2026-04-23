from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_garch_service
from app.schemas.garch import GarchResponse
from app.services.garch_service import GarchService

router = APIRouter()


@router.get("/{ticker}", summary="Analisis ARCH GARCH EGARCH", response_model=GarchResponse)
async def get_garch_analysis(
    ticker: str,
    start: str = Query(default="2021-01-01"),
    end: str = Query(default="2026-12-31"),
    return_type: str = Query(default="log"),
    mode: str = Query(default="estadistico"),
    forecast_horizon: int = Query(default=5, ge=1, le=10),
    service: GarchService = Depends(get_garch_service),
) -> GarchResponse:
    try:
        result = service.analyze(
            ticker=ticker,
            start=start,
            end=end,
            return_type=return_type,
            mode=mode,
            forecast_horizon=forecast_horizon,
        )
        return GarchResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc