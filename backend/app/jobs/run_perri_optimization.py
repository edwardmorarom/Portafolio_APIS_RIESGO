from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.db.database import SessionLocal, init_db
from app.services.perri_optimizer_service import PerriOptimizerService


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = PROJECT_ROOT / "backend" / "data" / "perri_latest_optimization.json"


def _json_default(value: Any) -> str:
    return str(value)


def run_perri_optimization_job(
    history_years: int = 5,
    rf_annual: float = 0.04,
) -> dict:
    """
    Ejecuta la optimización institucional de Perri y guarda el resultado en JSON.

    Este job está pensado para ser ejecutado manualmente o desde GitHub Actions
    después de actualizar los precios históricos.
    """
    init_db()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as db:
        service = PerriOptimizerService()
        result = service.run_optimization(
            db=db,
            history_years=history_years,
            rf_annual=rf_annual,
        )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "job": "run_perri_optimization",
        "history_years": int(history_years),
        "rf_annual": float(rf_annual),
        "result": result,
    }

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            payload,
            file,
            ensure_ascii=False,
            indent=2,
            default=_json_default,
        )

    return {
        "status": "ok",
        "output_path": str(OUTPUT_PATH),
        "eligible_assets": result["eligible_assets"],
        "assets_with_valid_returns": result["assets_with_valid_returns"],
        "min_risk_sharpe": result["min_risk"]["sharpe"],
        "max_sharpe": result["max_sharpe"]["sharpe"],
    }


def main() -> None:
    result = run_perri_optimization_job()

    print("OK: optimización Perri guardada en JSON")
    print(f"OK: archivo: {result['output_path']}")
    print(f"OK: activos elegibles: {result['eligible_assets']}")
    print(f"OK: activos con retornos válidos: {result['assets_with_valid_returns']}")
    print(f"OK: Sharpe mínimo riesgo: {result['min_risk_sharpe']}")
    print(f"OK: Sharpe máximo Sharpe: {result['max_sharpe']}")


if __name__ == "__main__":
    main()
