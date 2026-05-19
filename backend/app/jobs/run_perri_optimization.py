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


def _primary_metrics(result: dict) -> dict:
    """
    Extrae el caso principal usado como referencia:
    5 años / 15 activos exactos.
    """
    primary = result["horizons"]["5y"]["portfolio_sizes"]["15"]

    return {
        "min_risk_sharpe": primary["min_risk"]["sharpe"],
        "max_sharpe_sharpe": primary["max_sharpe"]["sharpe"],
        "max_return_sharpe": primary["max_return"]["sharpe"],
        "min_risk_return": primary["min_risk"]["expected_return_annual"],
        "max_sharpe_return": primary["max_sharpe"]["expected_return_annual"],
        "max_return_return": primary["max_return"]["expected_return_annual"],
        "min_risk_volatility": primary["min_risk"]["volatility_annual"],
        "max_sharpe_volatility": primary["max_sharpe"]["volatility_annual"],
        "max_return_volatility": primary["max_return"]["volatility_annual"],
    }


def run_perri_optimization_job(
    history_years: int = 5,
    rf_annual: float = 0.04,
) -> dict:
    """
    Ejecuta la optimización institucional de Perri y guarda el resultado en JSON.

    Este job está pensado para ejecución manual o desde GitHub Actions después
    de actualizar los precios históricos.
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

    metrics = _primary_metrics(result)

    return {
        "status": "ok",
        "output_path": str(OUTPUT_PATH),
        "eligible_assets": result["eligible_assets"],
        "assets_with_valid_returns": result["assets_with_valid_returns"],
        "horizon_keys": result["horizon_keys"],
        "portfolio_sizes": result["portfolio_sizes"],
        "objectives": result["objectives"],
        **metrics,
    }


def main() -> None:
    result = run_perri_optimization_job()

    print("OK: optimización Perri guardada en JSON")
    print(f"OK: archivo: {result['output_path']}")
    print(f"OK: activos elegibles: {result['eligible_assets']}")
    print(f"OK: activos con retornos válidos: {result['assets_with_valid_returns']}")
    print(f"OK: horizontes calculados: {', '.join(result['horizon_keys'])}")
    print(
        "OK: tamaños exactos: "
        + ", ".join(str(size) for size in result["portfolio_sizes"])
    )
    print(f"OK: objetivos: {', '.join(result['objectives'])}")
    print("OK: referencia principal: 5y / 15 activos exactos")
    print(
        "OK: min_risk | "
        f"retorno={result['min_risk_return']:.6f} | "
        f"volatilidad={result['min_risk_volatility']:.6f} | "
        f"Sharpe={result['min_risk_sharpe']:.6f}"
    )
    print(
        "OK: max_sharpe | "
        f"retorno={result['max_sharpe_return']:.6f} | "
        f"volatilidad={result['max_sharpe_volatility']:.6f} | "
        f"Sharpe={result['max_sharpe_sharpe']:.6f}"
    )
    print(
        "OK: max_return | "
        f"retorno={result['max_return_return']:.6f} | "
        f"volatilidad={result['max_return_volatility']:.6f} | "
        f"Sharpe={result['max_return_sharpe']:.6f}"
    )


if __name__ == "__main__":
    main()
