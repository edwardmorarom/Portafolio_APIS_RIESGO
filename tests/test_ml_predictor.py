from fastapi.testclient import TestClient

from app.main import app
from app.ml.predictor import MLPredictor


def test_ml_predictor_singleton_instance():
    assert MLPredictor() is MLPredictor()


def test_ml_predictor_model_is_loaded():
    predictor = MLPredictor()

    assert predictor.is_loaded() is True
    assert predictor.metadata()["model_loaded"] is True
    assert predictor.metadata()["model_size_bytes"] > 0
    assert predictor.metadata()["singleton"] is True
    assert predictor.metadata()["model_type"] == "LinearRegression"


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


def test_ml_status_endpoint_returns_metadata():
    client = TestClient(app)

    response = client.get("/api/v1/ml/status")

    assert response.status_code == 200
    payload = response.json()

    assert payload["model_loaded"] is True
    assert payload["model_version"] == "1.0.0"
    assert payload["model_size_bytes"] > 0


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

    assert payload["model_version"] == "1.0.0"
    assert payload["model_type"] == "LinearRegression"
    assert payload["target"] == "Retorno esperado del portafolio"
    assert isinstance(payload["predicted_return"], float)
    assert payload["interpretation"]
