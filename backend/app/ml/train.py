from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso, Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"


def generate_training_data():
    rng = np.random.default_rng(42)

    samples = 500

    volatility = rng.uniform(0.05, 0.60, samples)
    sharpe_ratio = rng.uniform(-1.0, 3.0, samples)
    var_95 = rng.uniform(-0.30, -0.01, samples)
    beta = rng.uniform(0.5, 2.0, samples)
    market_return = rng.uniform(-0.15, 0.25, samples)
    horizon_months = rng.choice([1, 3, 6, 12, 24, 36], samples)

    X = np.column_stack([
        volatility,
        sharpe_ratio,
        var_95,
        beta,
        market_return,
        horizon_months,
    ])

    annual_return = (
        (market_return * 0.4)
        + (sharpe_ratio * 0.08)
        - (volatility * 0.15)
        + (beta * 0.03)
        + (var_95 * 0.1)
    )

    noise = rng.normal(0, 0.02, samples)
    annual_return = annual_return + noise
    y = np.power(1 + annual_return, horizon_months / 12.0) - 1

    return X, y


def train_model():
    X, y = generate_training_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    models = {
        "ridge": Ridge(alpha=1.0),
        "lasso": Lasso(alpha=0.001, max_iter=10000),
        "gradient_boosting": GradientBoostingRegressor(random_state=42, n_estimators=120, max_depth=3),
    }

    metrics = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        metrics[name] = {
            "r2": float(r2_score(y_test, pred)),
            "mae": float(mean_absolute_error(y_test, pred)),
        }

    artifact = {
        "models": models,
        "metrics": metrics,
        "target": "Retorno acumulado a horizonte fijo",
        "features": ["volatility", "sharpe_ratio", "var_95", "beta", "market_return", "horizon_months"],
        "training_samples": int(len(X)),
    }

    joblib.dump(artifact, MODEL_PATH)

    print(f"Modelo entrenado y guardado en: {MODEL_PATH}")


if __name__ == "__main__":
    train_model()
