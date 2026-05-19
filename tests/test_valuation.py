from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_nelson_siegel_curve_fit():
    response = client.post(
        "/api/v1/valuation/nelson-siegel",
        json={
            "yields": [0.03, 0.035, 0.04, 0.045],
            "maturities": [1, 2, 5, 10],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "params" in data
    assert "rmse" in data
    assert data["curve_type"] == "Nelson-Siegel"


def test_black_scholes_call_option():
    response = client.post(
        "/api/v1/valuation/black-scholes",
        json={
            "spot_price": 100,
            "strike_price": 105,
            "time_to_maturity": 1,
            "risk_free_rate": 0.05,
            "volatility": 0.2,
            "option_type": "call",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "price" in data
    assert "greeks" in data
    assert data["price"] > 0


def test_black_scholes_put_option():
    response = client.post(
        "/api/v1/valuation/black-scholes",
        json={
            "spot_price": 100,
            "strike_price": 95,
            "time_to_maturity": 1,
            "risk_free_rate": 0.05,
            "volatility": 0.25,
            "option_type": "put",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["price"] > 0
