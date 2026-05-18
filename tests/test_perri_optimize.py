from pathlib import Path
import sys

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


def test_perri_optimize_returns_valid_portfolios():
    with TestClient(app) as client:
        response = client.get("/api/v1/perri/optimize?history_years=5&rf_annual=0.04")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["eligible_assets"] > 0
    assert payload["assets_with_valid_returns"] > 0
    assert payload["history_years"] == 5
    assert payload["rf_annual"] == 0.04

    assert "min_risk" in payload
    assert "max_sharpe" in payload

    min_risk = payload["min_risk"]
    max_sharpe = payload["max_sharpe"]

    assert min_risk["objective"] == "min_risk"
    assert max_sharpe["objective"] == "max_sharpe"

    assert min_risk["volatility_annual"] >= 0
    assert max_sharpe["volatility_annual"] >= 0

    assert len(min_risk["weights"]) > 0
    assert len(max_sharpe["weights"]) > 0

    min_risk_weight_sum = sum(item["weight"] for item in min_risk["weights"])
    max_sharpe_weight_sum = sum(item["weight"] for item in max_sharpe["weights"])

    assert 0.99 <= min_risk_weight_sum <= 1.01
    assert 0.99 <= max_sharpe_weight_sum <= 1.01
