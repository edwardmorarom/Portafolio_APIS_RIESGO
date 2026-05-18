from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.db.database import SessionLocal, init_db
from app.db.models import Asset, Price
from app.db.seed_db import seed_base_assets, seed_perri_assets


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CACHE_PATH = PROJECT_ROOT / "roboadvisor_cache.csv"
CHUNK_SIZE = 80


def _chunks(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _normalize_date(value: Any) -> date:
    return pd.to_datetime(value).date()


def import_perri_prices(cache_path: Path = CACHE_PATH) -> dict[str, int]:
    """
    Importa cierres históricos desde roboadvisor_cache.csv hacia SQLite.

    La tabla Price guarda:
    - cierre original
    - moneda original
    - tasa FX histórica a USD
    - cierre convertido a USD
    - cierre compatible close = close_usd

    En esta primera carga, el universo Perri está en USD, por lo que:
    fx_rate_to_usd = 1.0
    close_usd = close_original
    """
    init_db()

    if not cache_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de cache: {cache_path}")

    # Garantiza que los activos existan antes de cargar precios.
    seed_base_assets()
    seed_perri_assets()

    df = pd.read_csv(cache_path, index_col=0)
    df.index = [_normalize_date(value) for value in df.index]

    tickers = [str(col).strip().upper() for col in df.columns if str(col).strip()]

    with SessionLocal() as db:
        assets = list(
            db.scalars(
                select(Asset).where(Asset.ticker.in_(tickers))
            )
        )

        asset_by_ticker = {asset.ticker: asset for asset in assets}

        missing_assets = sorted(set(tickers) - set(asset_by_ticker.keys()))
        skipped_non_usd = 0
        prepared_rows = 0
        inserted_rows = 0

        rows: list[dict[str, Any]] = []

        for ticker in tickers:
            asset = asset_by_ticker.get(ticker)

            if asset is None:
                continue

            original_currency = asset.currency or "USD"

            # El cache actual de Perri está en USD.
            # Cuando entren tickers no USD, se debe cargar FX histórico antes de insertar precios.
            if original_currency != "USD":
                skipped_non_usd += 1
                continue

            series = df[ticker].dropna()

            for price_date, close_value in series.items():
                if pd.isna(close_value):
                    continue

                close_original = float(close_value)
                fx_rate_to_usd = 1.0
                close_usd = close_original * fx_rate_to_usd

                rows.append(
                    {
                        "asset_id": asset.id,
                        "date": price_date,
                        "close_original": close_original,
                        "original_currency": original_currency,
                        "fx_ticker": None,
                        "fx_rate_to_usd": fx_rate_to_usd,
                        "close_usd": close_usd,
                        "close": close_usd,
                        "source": "roboadvisor_cache.csv",
                    }
                )

                prepared_rows += 1

        for chunk in _chunks(rows, CHUNK_SIZE):
            statement = sqlite_insert(Price).values(chunk)
            statement = statement.on_conflict_do_nothing(
                index_elements=["asset_id", "date"]
            )
            result = db.execute(statement)

            if result.rowcount and result.rowcount > 0:
                inserted_rows += int(result.rowcount)

        db.commit()

        total_prices = db.scalar(select(func.count()).select_from(Price)) or 0

    return {
        "tickers_in_cache": len(tickers),
        "missing_assets": len(missing_assets),
        "skipped_non_usd_assets": skipped_non_usd,
        "prepared_rows": prepared_rows,
        "inserted_rows": inserted_rows,
        "total_prices_in_db": int(total_prices),
    }


def main() -> None:
    result = import_perri_prices()

    print("OK: importación de cierres históricos finalizada")
    print(f"OK: tickers en cache: {result['tickers_in_cache']}")
    print(f"OK: activos no encontrados en SQLite: {result['missing_assets']}")
    print(f"OK: activos no USD omitidos: {result['skipped_non_usd_assets']}")
    print(f"OK: filas preparadas: {result['prepared_rows']}")
    print(f"OK: filas nuevas insertadas: {result['inserted_rows']}")
    print(f"OK: total precios en SQLite: {result['total_prices_in_db']}")


if __name__ == "__main__":
    main()
