from pathlib import Path
from typing import Any

import joblib
import numpy as np


MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"
MODEL_VERSION = "3.0.0"
MODEL_TYPE = "IsolationForest/OneClassSVM"
MODEL_TARGET = "Deteccion de anomalias en retornos"
MODEL_FEATURES = ["return", "abs_return", "rolling_mean_5", "rolling_vol_5", "zscore_20"]


class MLPredictor:
    _instance = None
    _artifact: dict[str, Any] | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._load_model()
            print(f"[MLPredictor] modelo cargado: {MODEL_TYPE}")
        return cls._instance

    @classmethod
    def _load_model(cls) -> None:
        if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0:
            loaded = joblib.load(MODEL_PATH)
            if isinstance(loaded, dict) and "models" in loaded:
                cls._artifact = loaded

    def is_loaded(self) -> bool:
        return self._artifact is not None

    @property
    def model_version(self) -> str:
        return str((self._artifact or {}).get("version") or MODEL_VERSION)

    def metadata(self) -> dict:
        return {
            "model_loaded": self.is_loaded(),
            "model_version": self.model_version,
            "model_type": MODEL_TYPE,
            "target": MODEL_TARGET,
            "features": MODEL_FEATURES,
            "metrics": (self._artifact or {}).get("metrics", {}),
            "available_models": list((self._artifact or {}).get("models", {}).keys()),
            "singleton": True,
            "model_path": str(MODEL_PATH),
            "model_size_bytes": MODEL_PATH.stat().st_size if MODEL_PATH.exists() else 0,
        }

    @staticmethod
    def build_features(returns: list[float] | np.ndarray) -> np.ndarray:
        values = np.asarray(returns, dtype=float)
        rows = []
        for index, value in enumerate(values):
            w5 = values[max(0, index - 4) : index + 1]
            w20 = values[max(0, index - 19) : index + 1]
            vol20 = float(np.std(w20)) if len(w20) > 1 else 0.0
            zscore = 0.0 if vol20 == 0 else (float(value) - float(np.mean(w20))) / vol20
            rows.append(
                [
                    float(value),
                    abs(float(value)),
                    float(np.mean(w5)),
                    float(np.std(w5)) if len(w5) > 1 else 0.0,
                    float(zscore),
                ]
            )
        return np.asarray(rows, dtype=float)

    def predict(self, returns: list[float], ticker: str = "PORTFOLIO") -> dict:
        if self._artifact is None:
            raise ValueError("El modelo ML no ha sido entrenado.")

        models = self._artifact.get("models", {})
        isolation = models.get("isolation_forest")
        svm = models.get("one_class_svm")
        if isolation is None or svm is None:
            raise ValueError("El artefacto ML no contiene modelos de anomalias.")

        X = self.build_features(returns)
        isolation_pred = isolation.predict(X)
        svm_pred = svm.predict(X)
        isolation_score = isolation.decision_function(X)
        svm_score = svm.decision_function(X)

        points = []
        for index, value in enumerate(returns):
            iso_anomaly = bool(isolation_pred[index] == -1)
            svm_anomaly = bool(svm_pred[index] == -1)
            points.append(
                {
                    "index": index,
                    "return_value": float(value),
                    "isolation_forest_score": float(isolation_score[index]),
                    "one_class_svm_score": float(svm_score[index]),
                    "is_anomaly_isolation_forest": iso_anomaly,
                    "is_anomaly_one_class_svm": svm_anomaly,
                    "is_anomaly_consensus": bool(iso_anomaly and svm_anomaly),
                }
            )

        anomalies_if = sum(point["is_anomaly_isolation_forest"] for point in points)
        anomalies_svm = sum(point["is_anomaly_one_class_svm"] for point in points)
        anomalies_consensus = sum(point["is_anomaly_consensus"] for point in points)
        if anomalies_consensus:
            interpretation = (
                f"{ticker}: se detectaron {anomalies_consensus} retornos anomalos por consenso; "
                "conviene revisar eventos de mercado, liquidez o errores de dato."
            )
        else:
            interpretation = f"{ticker}: no hay anomalias por consenso entre Isolation Forest y One-Class SVM."

        return {
            "ticker": ticker.strip().upper() or "PORTFOLIO",
            "model_version": self.model_version,
            "model_type": MODEL_TYPE,
            "target": MODEL_TARGET,
            "observations": len(points),
            "anomalies_isolation_forest": int(anomalies_if),
            "anomalies_one_class_svm": int(anomalies_svm),
            "anomalies_consensus": int(anomalies_consensus),
            "points": points,
            "interpretation": interpretation,
        }
