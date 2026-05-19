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

def test_black_scholes_returns_five_greeks():
    response = client.post(
        "/api/v1/valuation/black-scholes",
        json={
            "spot_price": 100,
            "strike_price": 100,
            "time_to_maturity": 1,
            "risk_free_rate": 0.05,
            "volatility": 0.2,
            "option_type": "call",
        },
    )

    assert response.status_code == 200

    greeks = response.json()["greeks"]

    assert set(greeks.keys()) == {"delta", "gamma", "vega", "theta", "rho"}


def test_black_scholes_put_call_parity():
    call_response = client.post(
        "/api/v1/valuation/black-scholes",
        json={
            "spot_price": 100,
            "strike_price": 100,
            "time_to_maturity": 1,
            "risk_free_rate": 0.05,
            "volatility": 0.2,
            "option_type": "call",
        },
    )

    put_response = client.post(
        "/api/v1/valuation/black-scholes",
        json={
            "spot_price": 100,
            "strike_price": 100,
            "time_to_maturity": 1,
            "risk_free_rate": 0.05,
            "volatility": 0.2,
            "option_type": "put",
        },
    )

    assert call_response.status_code == 200
    assert put_response.status_code == 200

    call_price = call_response.json()["price"]
    put_price = put_response.json()["price"]

    parity_value = 100 - 100 * __import__("math").exp(-0.05 * 1)

    assert abs((call_price - put_price) - parity_value) < 1e-6

def test_bond_metrics_endpoint():
    response = client.post(
        "/api/v1/valuation/bond-metrics",
        json={
            "face_value": 1000,
            "coupon_rate": 0.05,
            "maturity_years": 5,
            "market_yield": 0.04,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["price"] > 0
    assert data["duration"] > 0
    assert data["modified_duration"] > 0
    assert data["convexity"] > 0
