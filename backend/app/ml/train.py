from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LinearRegression


MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"


def generate_training_data():
    rng = np.random.default_rng(42)

    samples = 500

    volatility = rng.uniform(0.05, 0.60, samples)
    sharpe_ratio = rng.uniform(-1.0, 3.0, samples)
    var_95 = rng.uniform(-0.30, -0.01, samples)
    beta = rng.uniform(0.5, 2.0, samples)
    market_return = rng.uniform(-0.15, 0.25, samples)

    X = np.column_stack([
        volatility,
        sharpe_ratio,
        var_95,
        beta,
        market_return,
    ])

    y = (
        (market_return * 0.4)
        + (sharpe_ratio * 0.08)
        - (volatility * 0.15)
        + (beta * 0.03)
        + (var_95 * 0.1)
    )

    noise = rng.normal(0, 0.02, samples)

    y = y + noise

    return X, y


def train_model():
    X, y = generate_training_data()

    model = LinearRegression()

    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)

    print(f"Modelo entrenado y guardado en: {MODEL_PATH}")


if __name__ == "__main__":
    train_model()
