from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_returns_stats_service
from app.schemas.returns_stats import ReturnsStatsResponse
from app.services.returns_stats_service import ReturnsStatsService

router = APIRouter()


@router.get("/summary/{ticker}", summary="Estadistica de rendimientos", response_model=ReturnsStatsResponse)
async def get_returns_stats(
    ticker: str,
    start: str = Query(default="2021-01-01"),
    end: str = Query(default="2026-12-31"),
    return_type: str = Query(default="log"),
    mode: str = Query(default="estadistico"),
    service: ReturnsStatsService = Depends(get_returns_stats_service),
) -> ReturnsStatsResponse:
    try:
        result = service.build_returns_stats(
            ticker=ticker,
            start=start,
            end=end,
            return_type=return_type,
            mode=mode,
        )
        return ReturnsStatsResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc