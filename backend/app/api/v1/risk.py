from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_risk_service
from app.schemas.risk import PortfolioVarRequest, PortfolioVarResponse
from app.services.risk_service import RiskService
from app.core.security import require_internal_api_key

router = APIRouter()


@router.post("/var", summary="Calcular VaR y CVaR del portafolio", response_model=PortfolioVarResponse)
async def calculate_var(
    payload: PortfolioVarRequest,
    _: None = Depends(require_internal_api_key),
    service: RiskService = Depends(get_risk_service),
) -> PortfolioVarResponse:
    try:
        result = service.calculate_var(
            tickers=payload.tickers,
            weights=payload.weights,
            start=payload.start,
            end=payload.end,
            alpha=payload.alpha,
            n_sim=payload.n_sim,
            return_type=payload.return_type,
            distribution=payload.distribution,
        )
        return PortfolioVarResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
