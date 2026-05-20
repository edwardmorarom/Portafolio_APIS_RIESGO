from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.main import app


def test_investor_preferences_accepts_2y_horizon():
    client = TestClient(app)

    response = client.post(
        "/api/v1/investor/preferences",
        json={
            "tickers": ["AAPL", "MSFT"],
            "weights_pct": [60.0, 40.0],
            "base_currency": "USD",
            "confidence_level": 0.95,
            "risk_profile": "moderado",
            "horizon_type": "2y",
            "return_type": "log",
            "mode": "general",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["tickers"] == ["AAPL", "MSFT"]
    assert payload["weights_pct"] == [60.0, 40.0]
    assert payload["weights_decimal"] == [0.6, 0.4]
    assert payload["base_currency"] == "USD"
    assert payload["risk_profile"] == "moderado"
    assert payload["horizon_type"] == "2y"

    start = date.fromisoformat(payload["start"])
    end = date.fromisoformat(payload["end"])

    assert (end - start).days == 365 * 2
