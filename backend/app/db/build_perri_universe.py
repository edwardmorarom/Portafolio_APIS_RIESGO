from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CACHE_PATH = PROJECT_ROOT / "roboadvisor_cache.csv"
OUTPUT_PATH = PROJECT_ROOT / "backend" / "data" / "perri_universe.json"


def build_perri_universe() -> dict:
    if not CACHE_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró roboadvisor_cache.csv en: {CACHE_PATH}"
        )

    df = pd.read_csv(CACHE_PATH, index_col=0)
    tickers = sorted({str(col).strip().upper() for col in df.columns if str(col).strip()})

    assets = [
        {
            "ticker": ticker,
            "name": ticker,
            "tipo_activo": "pendiente_clasificacion",
            "moneda_origen": "pendiente",
            "fx_ticker": None,
            "incluir_en_perri": True,
            "fuente": "roboadvisor_cache.csv",
        }
        for ticker in tickers
    ]

    return {
        "nombre": "Universo institucional de Perri",
        "version": "1.0.0",
        "base_currency": "USD",
        "history_years": 5,
        "conversion_policy": (
            "Los precios deben conservar cierre original y cierre convertido a USD "
            "usando tasa FX histórica diaria cuando el activo no esté denominado en USD."
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": "roboadvisor_cache.csv",
        "total_assets": len(assets),
        "assets": assets,
    }


def main() -> None:
    universe = build_perri_universe()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(universe, file, ensure_ascii=False, indent=2)

    print(f"OK: JSON creado en {OUTPUT_PATH}")
    print(f"OK: activos registrados: {universe['total_assets']}")


if __name__ == "__main__":
    main()
