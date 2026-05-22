from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_portfolio_service
from app.db.models import Portfolio
from app.db.database import get_db
from app.schemas.portfolio import (
    EfficientFrontierRequest,
    EfficientFrontierResponse,
    SavedPortfolioCreateRequest,
    SavedPortfolioResponse,
)
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
            allow_short_selling=payload.allow_short_selling,
        )
        return EfficientFrontierResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/saved", summary="Guardar portafolio del usuario", response_model=SavedPortfolioResponse)
async def save_portfolio(
    payload: SavedPortfolioCreateRequest,
    _: None = Depends(require_internal_api_key),
    db: Session = Depends(get_db),
) -> SavedPortfolioResponse:
    record = Portfolio(
        name=payload.name,
        owner=payload.owner,
        description=payload.description,
        weights={
            "tickers": payload.tickers,
            "weights_pct": payload.weights_pct,
            "horizon": payload.horizon,
            "benchmark": payload.benchmark,
            "base_currency": payload.base_currency,
            "confidence_level": payload.confidence_level,
        },
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return SavedPortfolioResponse.model_validate(record)


@router.get("/saved", summary="Listar portafolios guardados", response_model=list[SavedPortfolioResponse])
async def list_saved_portfolios(
    owner: str | None = None,
    _: None = Depends(require_internal_api_key),
    db: Session = Depends(get_db),
) -> list[SavedPortfolioResponse]:
    stmt = select(Portfolio).order_by(Portfolio.created_at.desc())
    if owner:
        stmt = stmt.where(Portfolio.owner == owner)
    records = db.scalars(stmt).all()
    return [SavedPortfolioResponse.model_validate(record) for record in records]
