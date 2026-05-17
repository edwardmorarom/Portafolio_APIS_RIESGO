from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.db.models import Asset, Portfolio, PredictionLog, Price


router = APIRouter()


@router.get("/health")
def persistence_health(db: Session = Depends(get_db)) -> dict:
    """
    Valida que la conexión SQLAlchemy + SQLite esté disponible
    y que las tablas ORM principales puedan consultarse.
    """
    assets_count = db.scalar(select(func.count()).select_from(Asset)) or 0
    prices_count = db.scalar(select(func.count()).select_from(Price)) or 0
    portfolios_count = db.scalar(select(func.count()).select_from(Portfolio)) or 0
    predictions_count = db.scalar(select(func.count()).select_from(PredictionLog)) or 0

    return {
        "status": "ok",
        "database": "connected",
        "tables": {
            "assets": int(assets_count),
            "prices": int(prices_count),
            "portfolios": int(portfolios_count),
            "predictions_log": int(predictions_count),
        },
    }