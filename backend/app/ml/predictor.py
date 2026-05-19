from pathlib import Path

import joblib
import numpy as np


MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"


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
            [[
                volatility,
                sharpe_ratio,
                var_95,
                beta,
                market_return,
            ]]
        )

        prediction = self._model.predict(features)[0]

        return float(prediction)
