from pathlib import Path
import sys

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


client = TestClient(app)


def test_perri_latest_returns_precalculated_optimization():
    response = client.get("/api/v1/perri/latest")

    assert response.status_code == 200

    payload = response.json()

    assert payload["job"] == "run_perri_optimization"
    assert "generated_at_utc" in payload
    assert "result" in payload

    result = payload["result"]

    assert result["status"] == "ok"
    assert result["eligible_assets"] > 0
    assert result["assets_with_valid_returns"] > 0

    assert "min_risk" in result
    assert "max_sharpe" in result

    assert len(result["min_risk"]["weights"]) > 0
    assert len(result["max_sharpe"]["weights"]) > 0

    assert result["min_risk"]["volatility_annual"] >= 0
    assert result["max_sharpe"]["volatility_annual"] >= 0
