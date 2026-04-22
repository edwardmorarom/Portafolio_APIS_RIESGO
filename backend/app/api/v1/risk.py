from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_risk_service
from app.schemas.risk import PortfolioVarRequest, PortfolioVarResponse
from app.services.risk_service import RiskService

router = APIRouter()


@router.post("/var", summary="Calcular VaR y CVaR del portafolio", response_model=PortfolioVarResponse)
async def calculate_var(
    payload: PortfolioVarRequest,
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
        )
        return PortfolioVarResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc