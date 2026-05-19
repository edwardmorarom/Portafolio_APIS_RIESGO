from pathlib import Path
import sys

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


def test_perri_latest_contains_exact_horizons_sizes_and_objectives():
    with TestClient(app) as client:
        response = client.get("/api/v1/perri/latest")

    assert response.status_code == 200

    payload = response.json()
    result = payload["result"]

    assert result["status"] == "ok"
    assert result["horizon_keys"] == ["1y", "3y", "5y"]
    assert result["portfolio_sizes"] == [5, 10, 15]
    assert result["objectives"] == ["min_risk", "max_sharpe", "max_return"]

    for horizon in ["1y", "3y", "5y"]:
        assert horizon in result["horizons"]

        horizon_block = result["horizons"][horizon]
        assert "portfolio_sizes" in horizon_block

        for size in ["5", "10", "15"]:
            assert size in horizon_block["portfolio_sizes"]

            size_block = horizon_block["portfolio_sizes"][size]
            assert size_block["selection_mode"] == "exact"
            assert size_block["portfolio_size"] == int(size)

            for objective in ["min_risk", "max_sharpe", "max_return"]:
                assert objective in size_block

                portfolio = size_block[objective]

                assert portfolio["selection_mode"] == "exact"
                assert portfolio["portfolio_size"] == int(size)
                assert portfolio["selected_assets_count"] == int(size)
                assert len(portfolio["weights"]) == int(size)

                assert portfolio["expected_return_annual"] is not None
                assert portfolio["volatility_annual"] >= 0
                assert portfolio["sharpe"] is not None

                assert "beta" in portfolio
                assert "alpha_annual" in portfolio
                assert "benchmark_ticker" in portfolio

                weight_sum = sum(item["weight"] for item in portfolio["weights"])
                assert 0.99 <= weight_sum <= 1.01

                min_weight = portfolio["constraints"]["min_weight_per_asset"]
                for item in portfolio["weights"]:
                    assert item["weight"] >= min_weight - 1e-8
