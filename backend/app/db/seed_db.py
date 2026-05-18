from __future__ import annotations

from pathlib import Path

import pandas as pd
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


def _asset_exists(ticker: str) -> bool:
    with SessionLocal() as db:
        existing = db.scalar(select(Asset).where(Asset.ticker == ticker))
        return existing is not None


def seed_base_assets() -> int:
    """
    Inserta los 5 activos base del proyecto si no existen.
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


def seed_perri_assets(cache_path: str = "../roboadvisor_cache.csv") -> int:
    """
    Inserta en la tabla assets los tickers disponibles en roboadvisor_cache.csv.

    Este paso solo registra el universo institucional de Perri.
    No importa precios históricos todavía.
    """
    init_db()

    path = Path(cache_path)

    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de reserva institucional: {path.resolve()}"
        )

    df = pd.read_csv(path, index_col=0)
    tickers = [str(col).strip().upper() for col in df.columns if str(col).strip()]

    inserted = 0

    with SessionLocal() as db:
        for ticker in tickers:
            existing = db.scalar(select(Asset).where(Asset.ticker == ticker))

            if existing is not None:
                continue

            db.add(
                Asset(
                    ticker=ticker,
                    name=ticker,
                    sector="Reserva institucional Perri",
                    market="No especificado",
                    currency="USD",
                    country="No especificado",
                )
            )
            inserted += 1

        db.commit()

    return inserted


def count_assets() -> int:
    init_db()

    with SessionLocal() as db:
        result = db.scalars(select(Asset))
        return len(list(result))


def main() -> None:
    inserted_base = seed_base_assets()
    inserted_perri = seed_perri_assets()
    total_assets = count_assets()

    print(f"OK: activos base insertados: {inserted_base}")
    print(f"OK: activos Perri insertados: {inserted_perri}")
    print(f"OK: total de activos en SQLite: {total_assets}")


if __name__ == "__main__":
    main()