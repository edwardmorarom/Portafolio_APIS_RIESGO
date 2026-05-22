from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM


MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"
FEATURES = ["return", "abs_return", "rolling_mean_5", "rolling_vol_5", "zscore_20"]


def generate_return_series(samples: int = 900) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(42)
    returns = rng.normal(0.0004, 0.012, samples)

    turbulent_slice = slice(samples // 3, samples // 3 + 180)
    returns[turbulent_slice] = rng.normal(-0.0008, 0.028, len(returns[turbulent_slice]))

    anomaly_idx = rng.choice(np.arange(30, samples), size=36, replace=False)
    returns[anomaly_idx] += rng.choice([-1, 1], size=len(anomaly_idx)) * rng.uniform(0.055, 0.13, len(anomaly_idx))

    labels = np.zeros(samples, dtype=int)
    labels[anomaly_idx] = 1
    return returns, labels


def build_features(returns: np.ndarray) -> np.ndarray:
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


def main() -> None:
    returns, labels = generate_return_series()
    X = build_features(returns)
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_test = labels[split:]

    models = {
        "isolation_forest": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", IsolationForest(n_estimators=200, contamination=0.05, random_state=42)),
            ]
        ),
        "one_class_svm": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", OneClassSVM(kernel="rbf", gamma="scale", nu=0.05)),
            ]
        ),
    }

    metrics = {}
    for name, model in models.items():
        model.fit(X_train)
        predicted = (model.predict(X_test) == -1).astype(int)
        metrics[name] = classification_report(y_test, predicted, output_dict=True, zero_division=0)
        print(f"\n{name}")
        print(classification_report(y_test, predicted, zero_division=0))

    artifact = {
        "models": models,
        "metrics": metrics,
        "target": "Deteccion de anomalias en retornos",
        "features": FEATURES,
        "training_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "contamination": 0.05,
        "version": "3.0.0",
    }
    joblib.dump(artifact, MODEL_PATH)
    print(f"Modelo guardado: {MODEL_PATH}")


if __name__ == "__main__":
    main()
