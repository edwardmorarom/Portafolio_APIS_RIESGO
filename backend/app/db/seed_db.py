from __future__ import annotations

from sqlalchemy import select

from app.db.database import SessionLocal, init_db
from app.db.models import Asset


BASE_ASSETS = [
    {
        "ticker": "3382.T",
        "name": "Seven & i Holdings",
        "sector": "Consumer Defensive",
        "market": "Tokyo Stock Exchange",
        "currency": "JPY",
        "country": "Japan",
    },
    {
        "ticker": "ATD.TO",
        "name": "Alimentation Couche-Tard",
        "sector": "Consumer Defensive",
        "market": "Toronto Stock Exchange",
        "currency": "CAD",
        "country": "Canada",
    },
    {
        "ticker": "FEMSAUBD.MX",
        "name": "FEMSA",
        "sector": "Consumer Defensive",
        "market": "Mexican Stock Exchange",
        "currency": "MXN",
        "country": "Mexico",
    },
    {
        "ticker": "BP.L",
        "name": "BP",
        "sector": "Energy",
        "market": "London Stock Exchange",
        "currency": "GBP",
        "country": "United Kingdom",
    },
    {
        "ticker": "CA.PA",
        "name": "Carrefour",
        "sector": "Consumer Defensive",
        "market": "Euronext Paris",
        "currency": "EUR",
        "country": "France",
    },
]


def seed_assets() -> int:
    """
    Inserta los activos base del proyecto si no existen.
    Retorna la cantidad de activos nuevos insertados.
    """
    init_db()

    inserted = 0

    with SessionLocal() as db:
        for item in BASE_ASSETS:
            existing = db.scalar(
                select(Asset).where(Asset.ticker == item["ticker"])
            )

            if existing is not None:
                continue

            db.add(Asset(**item))
            inserted += 1

        db.commit()

    return inserted


if __name__ == "__main__":
    inserted_count = seed_assets()
    print(f"OK: activos insertados: {inserted_count}")