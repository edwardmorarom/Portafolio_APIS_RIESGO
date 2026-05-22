from fastapi.testclient import TestClient

from app.main import app
from app.ml.predictor import MLPredictor


def _sample_returns() -> list[float]:
    values = [0.001, -0.002, 0.003, 0.0005, -0.001, 0.002, 0.0015, -0.0012] * 5
    values[12] = -0.095
    values[31] = 0.082
    return values


def test_ml_predictor_singleton_instance():
    assert MLPredictor() is MLPredictor()


def test_ml_predictor_model_is_loaded():
    predictor = MLPredictor()

    assert predictor.is_loaded() is True
    assert predictor.metadata()["model_loaded"] is True
    assert predictor.metadata()["model_size_bytes"] > 0
    assert predictor.metadata()["singleton"] is True
    assert predictor.metadata()["model_type"] == "IsolationForest/OneClassSVM"
    assert "isolation_forest" in predictor.metadata()["available_models"]
    assert "one_class_svm" in predictor.metadata()["available_models"]


def test_ml_predictor_returns_anomaly_payload():
    predictor = MLPredictor()

    result = predictor.predict(returns=_sample_returns(), ticker="TEST")

    assert result["ticker"] == "TEST"
    assert result["target"] == "Deteccion de anomalias en retornos"
    assert result["observations"] == len(_sample_returns())
    assert result["anomalies_isolation_forest"] >= 1
    assert result["points"]


def test_ml_status_endpoint_returns_metadata():
    client = TestClient(app)

    response = client.get("/api/v1/ml/status")

    assert response.status_code == 200
    payload = response.json()

    assert payload["model_loaded"] is True
    assert payload["model_version"] == "3.0.0"
    assert payload["model_type"] == "IsolationForest/OneClassSVM"
    assert payload["model_size_bytes"] > 0


def test_ml_predict_endpoint_returns_anomaly_detection():
    client = TestClient(app)

    response = client.post(
        "/api/v1/ml/predict",
        json={
            "ticker": "TEST",
            "returns": _sample_returns(),
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["model_version"] == "3.0.0"
    assert payload["model_type"] == "IsolationForest/OneClassSVM"
    assert payload["target"] == "Deteccion de anomalias en retornos"
    assert payload["observations"] == len(_sample_returns())
    assert payload["points"]
    assert payload["interpretation"]
