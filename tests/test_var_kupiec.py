from pathlib import Path
import sys

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.dependencies import get_risk_service  # noqa: E402
from app.main import app  # noqa: E402
from app.services.risk_service import RiskService  # noqa: E402


class _Settings:
    min_obs_var = 60


class _FakeMarketClient:
    settings = _Settings()

    def get_prices(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        rng = np.random.default_rng(7 if ticker == "AAA" else 11)
        returns = rng.normal(0.0005, 0.012, 260)
        close = 100 * np.exp(np.cumsum(returns))
        return pd.DataFrame({"Close": close})


def test_risk_service_returns_kupiec_for_three_var_methods():
    service = RiskService(_FakeMarketClient())

    payload = service.calculate_var(
        tickers=["AAA", "BBB"],
        weights=[0.55, 0.45],
        start="2024-01-01",
        end="2025-01-01",
        alpha=0.95,
        n_sim=5000,
        return_type="log",
        distribution="normal",
    )

    assert set(payload["kupiec_tests"].keys()) == {"historical", "parametric", "monte_carlo"}

    for key in ["historical", "parametric", "monte_carlo"]:
        result = payload["kupiec_tests"][key]
        assert result["observations"] > 0
        assert result["expected_violations"] > 0
        assert result["lr_stat"] >= 0
        assert 0 <= result["p_value"] <= 1
        assert result["decision"] in {
            "No se rechaza cobertura adecuada",
            "Se rechaza cobertura adecuada",
        }
        assert result["interpretation"]


def test_var_endpoint_exposes_kupiec_tests_with_dependency_override():
    app.dependency_overrides[get_risk_service] = lambda: RiskService(_FakeMarketClient())
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/risk/var",
                json={
                    "tickers": ["AAA", "BBB"],
                    "weights": [0.5, 0.5],
                    "start": "2024-01-01",
                    "end": "2025-01-01",
                    "alpha": 0.95,
                    "n_sim": 5000,
                    "return_type": "log",
                    "distribution": "normal",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert set(data["kupiec_tests"].keys()) == {"historical", "parametric", "monte_carlo"}
    assert data["kupiec_test"]["method"] == "VaR histórico"
