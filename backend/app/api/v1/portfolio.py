from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_portfolio_service
from app.schemas.portfolio import EfficientFrontierRequest, EfficientFrontierResponse
from app.services.portfolio_service import PortfolioService
from app.core.security import require_internal_api_key

router = APIRouter()


@router.post(
    "/efficient-frontier",
    summary="Construir frontera eficiente",
    response_model=EfficientFrontierResponse,
)
async def efficient_frontier(
    payload: EfficientFrontierRequest,
    _: None = Depends(require_internal_api_key),
    service: PortfolioService = Depends(get_portfolio_service),
) -> EfficientFrontierResponse:
    try:
        result = service.build_efficient_frontier(
            tickers=payload.tickers,
            start=payload.start,
            end=payload.end,
            rf_annual=payload.rf_annual,
            n_portfolios=payload.n_portfolios,
            return_type=payload.return_type,
            target_return_annual=payload.target_return_annual,
            risk_profile=payload.risk_profile,
        )
        return EfficientFrontierResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc