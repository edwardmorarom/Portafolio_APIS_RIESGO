from pathlib import Path

import joblib
import numpy as np


MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"
MODEL_VERSION = "2.0.0"
MODEL_TYPE = "Ridge/Lasso/GradientBoostingRegressor"
MODEL_TARGET = "Predicción de retorno acumulado a horizonte fijo"
MODEL_FEATURES = ["volatility", "sharpe_ratio", "var_95", "beta", "market_return", "horizon_months"]
MODEL_METRICS = {
    "training_samples": 500,
    "validation": "Train/test split reproducible con semilla 42",
    "expected_use": "Apoyo predictivo académico para retorno acumulado; no es señal causal ni recomendación automática.",
}


class MLPredictor:
    _instance = None
    _artifact = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._load_model()
        return cls._instance

    @classmethod
    def _load_model(cls):
        if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0:
            loaded = joblib.load(MODEL_PATH)
            if isinstance(loaded, dict) and "models" in loaded:
                cls._artifact = loaded
            else:
                cls._artifact = {
                    "models": {"ridge": loaded},
                    "metrics": {"ridge": {"r2": None, "mae": None}},
                    "target": MODEL_TARGET,
                    "features": ["volatility", "sharpe_ratio", "var_95", "beta", "market_return"],
                    "legacy": True,
                }

    def is_loaded(self) -> bool:
        return self._artifact is not None

    def metadata(self) -> dict:
        metrics = dict(MODEL_METRICS)
        if self._artifact:
            metrics.update(self._artifact.get("metrics", {}))
            metrics["training_samples"] = self._artifact.get("training_samples", metrics["training_samples"])

        return {
            "model_loaded": self.is_loaded(),
            "model_version": MODEL_VERSION,
            "model_type": MODEL_TYPE,
            "target": MODEL_TARGET,
            "features": MODEL_FEATURES,
            "metrics": metrics,
            "available_models": list((self._artifact or {}).get("models", {}).keys()),
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
        horizon_months: int = 12,
        model_name: str = "gradient_boosting",
    ) -> float:
        if self._artifact is None:
            raise ValueError("El modelo ML no ha sido entrenado.")

        models = self._artifact.get("models", {})
        if model_name not in models:
            model_name = "gradient_boosting" if "gradient_boosting" in models else next(iter(models))

        feature_names = self._artifact.get("features", MODEL_FEATURES)
        raw = {
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "var_95": var_95,
            "beta": beta,
            "market_return": market_return,
            "horizon_months": horizon_months,
        }
        features = np.array([[raw[name] for name in feature_names]])
        return float(models[model_name].predict(features)[0])

    def predict_all(
        self,
        volatility: float,
        sharpe_ratio: float,
        var_95: float,
        beta: float,
        market_return: float,
        horizon_months: int = 12,
    ) -> dict[str, float]:
        if self._artifact is None:
            raise ValueError("El modelo ML no ha sido entrenado.")

        return {
            name: self.predict(
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                var_95=var_95,
                beta=beta,
                market_return=market_return,
                horizon_months=horizon_months,
                model_name=name,
            )
            for name in self._artifact.get("models", {})
        }
