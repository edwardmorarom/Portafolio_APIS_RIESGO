from fastapi.testclient import TestClient

from app.main import app
from app.ml.predictor import MLPredictor


def test_ml_predictor_singleton_instance():
    first = MLPredictor()
    second = MLPredictor()

    assert first is second


def test_ml_predictor_returns_float_prediction():
    predictor = MLPredictor()

    result = predictor.predict(
        volatility=0.22,
        sharpe_ratio=1.15,
        var_95=-0.08,
        beta=1.10,
        market_return=0.12,
    )

    assert isinstance(result, float)


def test_ml_predict_endpoint_returns_prediction():
    client = TestClient(app)

    response = client.post(
        "/api/v1/ml/predict",
        json={
            "volatility": 0.22,
            "sharpe_ratio": 1.15,
            "var_95": -0.08,
            "beta": 1.10,
            "market_return": 0.12,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert "predicted_return" in payload
    assert "model_version" in payload
    assert payload["model_version"] == "1.0.0"
    assert isinstance(payload["predicted_return"], float)
