from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_stress_testing_endpoint():
    response = client.post(
        "/api/v1/stress/scenario",
        json={
            "portfolio_value": 100000,
            "expected_return": 0.12,
            "volatility": 0.20,
            "var_95": -0.08,
            "beta": 1.15,
            "rate_shock": 0.03,
            "market_shock": -0.15,
            "benchmark_shock": -0.20,
            "volatility_multiplier": 1.5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "estimated_loss" in data
    assert "estimated_loss_pct" in data
    assert "benchmark_loss_pct" in data
    assert "interpretation" in data
    assert "severity" in data
    assert "summary" in data
    assert data["estimated_loss"] >= 0
    assert data["benchmark_loss_pct"] is not None
    assert data["relative_to_benchmark"]

