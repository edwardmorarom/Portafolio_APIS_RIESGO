from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.db.database import SessionLocal, init_db
from app.db.models import Asset


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PERRI_UNIVERSE_PATH = PROJECT_ROOT / "backend" / "data" / "perri_universe.json"


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


def _load_perri_universe() -> list[dict[str, Any]]:
    if not PERRI_UNIVERSE_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el universo oficial de Perri: {PERRI_UNIVERSE_PATH}"
        )

    with PERRI_UNIVERSE_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    assets = payload.get("assets", [])

    if not isinstance(assets, list):
        raise ValueError("El campo 'assets' de perri_universe.json no es una lista.")

    return assets


def seed_base_assets() -> tuple[int, int]:
    """
    Inserta o actualiza los 5 activos base del proyecto.

    Retorna:
    - insertados
    - actualizados
    """
    init_db()

    inserted = 0
    updated = 0

    with SessionLocal() as db:
        for item in BASE_ASSETS:
            ticker = item["ticker"]
            existing = db.scalar(select(Asset).where(Asset.ticker == ticker))

            if existing is None:
                db.add(Asset(**item))
                inserted += 1
                continue

            existing.name = item["name"]
            existing.sector = item["sector"]
            existing.market = item["market"]
            existing.currency = item["currency"]
            existing.country = item["country"]
            updated += 1

        db.commit()

    return inserted, updated


def seed_perri_assets() -> tuple[int, int]:
    """
    Inserta o actualiza los activos del universo oficial de Perri.

    Usa backend/data/perri_universe.json como fuente de verdad.
    Retorna:
    - insertados
    - actualizados
    """
    init_db()

    perri_assets = _load_perri_universe()

    inserted = 0
    updated = 0

    with SessionLocal() as db:
        for item in perri_assets:
            ticker = str(item["ticker"]).strip().upper()
            asset_type = str(item.get("tipo_activo", "pendiente_clasificacion"))
            currency = str(item.get("moneda_origen", "USD"))
            source = str(item.get("fuente", "perri_universe.json"))

            payload = {
                "ticker": ticker,
                "name": str(item.get("name") or ticker),
                "sector": f"Perri | {asset_type}",
                "market": source,
                "currency": currency,
                "country": "Global / US-listed",
            }

            existing = db.scalar(select(Asset).where(Asset.ticker == ticker))

            if existing is None:
                db.add(Asset(**payload))
                inserted += 1
                continue

            existing.name = payload["name"]
            existing.sector = payload["sector"]
            existing.market = payload["market"]
            existing.currency = payload["currency"]
            existing.country = payload["country"]
            updated += 1

        db.commit()

    return inserted, updated


def count_assets() -> int:
    init_db()

    with SessionLocal() as db:
        return len(list(db.scalars(select(Asset))))


def main() -> None:
    inserted_base, updated_base = seed_base_assets()
    inserted_perri, updated_perri = seed_perri_assets()
    total_assets = count_assets()

    print(f"OK: activos base insertados: {inserted_base}")
    print(f"OK: activos base actualizados: {updated_base}")
    print(f"OK: activos Perri insertados: {inserted_perri}")
    print(f"OK: activos Perri actualizados: {updated_perri}")
    print(f"OK: total de activos en SQLite: {total_assets}")


if __name__ == "__main__":
    main()
