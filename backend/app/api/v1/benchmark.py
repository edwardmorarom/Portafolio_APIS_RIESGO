from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_benchmark_service
from app.core.security import require_internal_api_key
from app.schemas.benchmark import BenchmarkCompareRequest, BenchmarkCompareResponse
from app.services.benchmark_service import BenchmarkService

router = APIRouter()


@router.post("/compare", summary="Comparar portafolio contra benchmark", response_model=BenchmarkCompareResponse)
async def compare_benchmark(
    payload: BenchmarkCompareRequest,
    _: None = Depends(require_internal_api_key),
    service: BenchmarkService = Depends(get_benchmark_service),
) -> BenchmarkCompareResponse:
    try:
        result = service.compare(
            tickers=payload.tickers,
            weights=payload.weights,
            benchmark_ticker=payload.benchmark_ticker,
            base_currency=payload.base_currency,
            start=payload.start,
            end=payload.end,
            return_type=payload.return_type,
            mode=payload.mode,
        )
        return BenchmarkCompareResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc