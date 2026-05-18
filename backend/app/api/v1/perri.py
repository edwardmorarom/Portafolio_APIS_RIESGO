from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.services.perri_optimizer_service import PerriOptimizerService


router = APIRouter()


@router.get("/optimize", summary="Optimización institucional automática de Perri")
async def optimize_perri_portfolio(
    history_years: int = Query(default=5, ge=1, le=10),
    rf_annual: float = Query(default=0.04, ge=0.0, le=1.0),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """
    Calcula automáticamente los portafolios institucionales de Perri:

    - mínimo riesgo
    - mejor relación riesgo-rentabilidad, usando Sharpe

    La fuente principal son los precios persistidos en SQLite.
    """
    try:
        service = PerriOptimizerService()
        return service.run_optimization(
            db=db,
            history_years=history_years,
            rf_annual=rf_annual,
            start=start,
            end=end,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
