from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_capm_service
from app.core.settings import get_settings
from app.schemas.capm import CapmResponse, PortfolioCapmRequest, PortfolioCapmResponse
from app.services.capm_service import CapmService

router = APIRouter()


@router.get("/{ticker}", summary="Calcular CAPM por activo", response_model=CapmResponse)
async def get_capm(
    ticker: str,
    start: str = Query(default="2021-01-01"),
    end: str = Query(default="2026-12-31"),
    base_currency: str = Query(default="USD"),
    benchmark_ticker: str | None = Query(default=None),
    service: CapmService = Depends(get_capm_service),
    return_type: str = Query(default="log"),
) -> CapmResponse:
    settings = get_settings()
    benchmark = benchmark_ticker or settings.global_benchmark

    try:
        result = service.calculate_capm(
            ticker=ticker,
            benchmark_ticker=benchmark,
            base_currency=base_currency,
            start=start,
            end=end,
            return_type=return_type,
        )
        return CapmResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/portfolio", summary="Calcular CAPM del portafolio", response_model=PortfolioCapmResponse)
async def get_portfolio_capm(
    payload: PortfolioCapmRequest,
    service: CapmService = Depends(get_capm_service),
) -> PortfolioCapmResponse:
    try:
        result = service.calculate_portfolio_capm(
            tickers=payload.tickers,
            weights=payload.weights,
            benchmark_ticker=payload.benchmark_ticker,
            base_currency=payload.base_currency,
            start=payload.start,
            end=payload.end,
            return_type=payload.return_type,
        )
        return PortfolioCapmResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc