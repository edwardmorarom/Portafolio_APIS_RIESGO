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
        "asset_type": "renta_variable",
        "benchmark_ticker": "ACWI",
        "benchmark_description": "MSCI ACWI ETF como referencia global de renta variable internacional.",
        "include_in_perri": True,
        "source": "base_assets",
    },
    {
        "ticker": "ATD.TO",
        "name": "Alimentation Couche-Tard",
        "sector": "Consumer Defensive",
        "market": "Toronto Stock Exchange",
        "currency": "CAD",
        "country": "Canada",
        "asset_type": "renta_variable",
        "benchmark_ticker": "ACWI",
        "benchmark_description": "MSCI ACWI ETF como referencia global de renta variable internacional.",
        "include_in_perri": True,
        "source": "base_assets",
    },
    {
        "ticker": "FEMSAUBD.MX",
        "name": "FEMSA",
        "sector": "Consumer Defensive",
        "market": "Mexican Stock Exchange",
        "currency": "MXN",
        "country": "Mexico",
        "asset_type": "renta_variable",
        "benchmark_ticker": "ACWI",
        "benchmark_description": "MSCI ACWI ETF como referencia global de renta variable internacional.",
        "include_in_perri": True,
        "source": "base_assets",
    },
    {
        "ticker": "BP.L",
        "name": "BP",
        "sector": "Energy",
        "market": "London Stock Exchange",
        "currency": "GBP",
        "country": "United Kingdom",
        "asset_type": "renta_variable",
        "benchmark_ticker": "ACWI",
        "benchmark_description": "MSCI ACWI ETF como referencia global de renta variable internacional.",
        "include_in_perri": True,
        "source": "base_assets",
    },
    {
        "ticker": "CA.PA",
        "name": "Carrefour",
        "sector": "Consumer Defensive",
        "market": "Euronext Paris",
        "currency": "EUR",
        "country": "France",
        "asset_type": "renta_variable",
        "benchmark_ticker": "ACWI",
        "benchmark_description": "MSCI ACWI ETF como referencia global de renta variable internacional.",
        "include_in_perri": True,
        "source": "base_assets",
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


def _upsert_asset(db, payload: dict[str, Any]) -> str:
    ticker = str(payload["ticker"]).strip().upper()
    existing = db.scalar(select(Asset).where(Asset.ticker == ticker))

    if existing is None:
        db.add(Asset(**payload))
        return "inserted"

    existing.name = payload.get("name")
    existing.sector = payload.get("sector")
    existing.market = payload.get("market")
    existing.currency = payload.get("currency")
    existing.country = payload.get("country")
    existing.asset_type = payload.get("asset_type")
    existing.benchmark_ticker = payload.get("benchmark_ticker")
    existing.benchmark_description = payload.get("benchmark_description")
    existing.include_in_perri = bool(payload.get("include_in_perri", False))
    existing.source = payload.get("source")

    return "updated"


def seed_base_assets() -> tuple[int, int]:
    """
    Inserta o actualiza los 5 activos base del proyecto.
    """
    init_db()

    inserted = 0
    updated = 0

    with SessionLocal() as db:
        for item in BASE_ASSETS:
            status = _upsert_asset(db, item)

            if status == "inserted":
                inserted += 1
            else:
                updated += 1

        db.commit()

    return inserted, updated


def seed_perri_assets() -> tuple[int, int]:
    """
    Inserta o actualiza los activos del universo oficial de Perri.
    Usa backend/data/perri_universe.json como fuente de verdad.
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
                "asset_type": asset_type,
                "benchmark_ticker": item.get("benchmark_ticker"),
                "benchmark_description": item.get("benchmark_descripcion"),
                "include_in_perri": bool(item.get("incluir_en_perri", True)),
                "source": source,
            }

            status = _upsert_asset(db, payload)

            if status == "inserted":
                inserted += 1
            else:
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
