from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.services.perri_optimizer_service import PerriOptimizerService


router = APIRouter()


@router.get("/latest", summary="Última optimización precalculada de Perri")
async def get_latest_perri_optimization() -> dict:
    """
    Devuelve el último resultado precalculado de Perri guardado en JSON.

    Este endpoint está pensado para dashboards y consultas rápidas sin recalcular
    Markowitz en cada petición.
    """
    output_path = Path(__file__).resolve().parents[3] / "data" / "perri_latest_optimization.json"

    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail="No existe optimización precalculada de Perri. Ejecuta app.jobs.run_perri_optimization.",
        )

    with output_path.open("r", encoding="utf-8") as file:
        return json.load(file)


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
