from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_decision_service
from app.schemas.decision import DecisionPanelRequest, DecisionPanelResponse
from app.services.decision_service import DecisionService
from app.core.security import require_internal_api_key

router = APIRouter()


@router.post("/panel", summary="Panel integrador de decisión", response_model=DecisionPanelResponse)
async def decision_panel(
    payload: DecisionPanelRequest,
    _: None = Depends(require_internal_api_key),
    service: DecisionService = Depends(get_decision_service),
) -> DecisionPanelResponse:
    try:
        result = service.build_panel(
            tickers=payload.tickers,
            weights=payload.weights,
            benchmark_ticker=payload.benchmark_ticker,
            base_currency=payload.base_currency,
            start=payload.start,
            end=payload.end,
            alpha=payload.alpha,
            n_sim=payload.n_sim,
            n_portfolios=payload.n_portfolios,
            return_type=payload.return_type,
        )
        return DecisionPanelResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc