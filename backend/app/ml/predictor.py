from pathlib import Path

import joblib
import numpy as np


MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"
MODEL_VERSION = "1.0.0"
MODEL_TYPE = "LinearRegression"
MODEL_TARGET = "Retorno esperado del portafolio"
MODEL_FEATURES = ["volatility", "sharpe_ratio", "var_95", "beta", "market_return"]
MODEL_METRICS = {
    "training_samples": 500,
    "validation": "Datos sintéticos reproducibles con semilla 42",
    "expected_use": "Apoyo predictivo académico, no señal causal ni recomendación automática",
}


class MLPredictor:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._load_model()
        return cls._instance

    @classmethod
    def _load_model(cls):
        if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0:
            cls._model = joblib.load(MODEL_PATH)

    def is_loaded(self) -> bool:
        return self._model is not None

    def metadata(self) -> dict:
        return {
            "model_loaded": self.is_loaded(),
            "model_version": MODEL_VERSION,
            "model_type": MODEL_TYPE,
            "target": MODEL_TARGET,
            "features": MODEL_FEATURES,
            "metrics": MODEL_METRICS,
            "singleton": True,
            "model_path": str(MODEL_PATH),
            "model_size_bytes": MODEL_PATH.stat().st_size if MODEL_PATH.exists() else 0,
        }

    def predict(
        self,
        volatility: float,
        sharpe_ratio: float,
        var_95: float,
        beta: float,
        market_return: float,
    ) -> float:
        if self._model is None:
            raise ValueError("El modelo ML no ha sido entrenado.")

        features = np.array(
            [[volatility, sharpe_ratio, var_95, beta, market_return]]
        )

        return float(self._model.predict(features)[0])
