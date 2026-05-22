from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.db.database import init_db
from app.db.models import Asset, MacroCache, Portfolio, PredictionLog, Price, SignalLog


router = APIRouter()


@router.get("/health")
def persistence_health(db: Session = Depends(get_db)) -> dict:
    """
    Valida que la conexión SQLAlchemy + SQLite esté disponible
    y que las tablas ORM principales puedan consultarse.
    """
    init_db()

    assets_count = db.scalar(select(func.count()).select_from(Asset)) or 0
    prices_count = db.scalar(select(func.count()).select_from(Price)) or 0
    portfolios_count = db.scalar(select(func.count()).select_from(Portfolio)) or 0
    predictions_count = db.scalar(select(func.count()).select_from(PredictionLog)) or 0
    signals_count = db.scalar(select(func.count()).select_from(SignalLog)) or 0
    macro_cache_count = db.scalar(select(func.count()).select_from(MacroCache)) or 0

    return {
        "status": "ok",
        "database": "connected",
        "tables": {
            "assets": int(assets_count),
            "prices": int(prices_count),
            "portfolios": int(portfolios_count),
            "predictions_log": int(predictions_count),
            "signals_log": int(signals_count),
            "macro_cache": int(macro_cache_count),
        },
    }
