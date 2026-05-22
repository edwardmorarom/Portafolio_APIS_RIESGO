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


def test_stress_testing_rubric_contract_multiple_scenarios():
    response = client.post(
        "/api/v1/stress",
        json={
            "portfolio_value": 100000,
            "expected_return": 0.10,
            "volatility": 0.18,
            "portfolio": [
                {"ticker": "AAA", "weight": 0.6, "beta": 1.1},
                {"ticker": "BOND", "weight": 0.4, "beta": 0.2, "duration": 5.0, "convexity": 30.0},
            ],
            "scenarios": [
                {"name": "Caida mercado -20%", "market_drop_pct": -0.20, "vol_multiplier": 1.0},
                {"name": "Shock tasa +200 pb", "rate_shock_bp": 200, "vol_multiplier": 1.0},
                {"name": "Volatilidad x2", "vol_multiplier": 2.0},
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "base_metrics" in data
    assert "stressed_metrics" in data
    assert len(data["stressed_metrics"]) == 3
    assert data["base_metrics"]["var_parametric_99"] > 0
    assert all("asset_impacts" in scenario for scenario in data["stressed_metrics"])
    assert all(len(scenario["asset_impacts"]) == 2 for scenario in data["stressed_metrics"])


def test_rate_shock_uses_fixed_income_duration_proxy():
    response = client.post(
        "/api/v1/stress",
        json={
            "portfolio_value": 100000,
            "expected_return": 0.05,
            "volatility": 0.12,
            "portfolio": [{"ticker": "TIP", "weight": 1.0, "beta": 0.1}],
            "scenarios": [{"name": "Shock tasa +200 pb", "rate_shock_bp": 200}],
        },
    )

    assert response.status_code == 200
    impact = response.json()["stressed_metrics"][0]["asset_impacts"][0]

    assert impact["price_change_pct"] < 0

