import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app.core.dependencies import get_alerts_service
from app.main import app
from app.services.alerts_service import AlertsService
from app.services.garch_service import GarchService
from app.services.portfolio_service import PortfolioService


client = TestClient(app)


def test_ewma_volatility_is_available_for_garch_methodology():
    series = pd.Series([0.5, -1.2, 0.8, -0.4, 1.1])
    volatility = GarchService._calculate_ewma_volatility(series, ewma_lambda=0.94)

    assert len(volatility) == len(series)
    assert all(value >= 0 for value in volatility)
    assert volatility[-1] > 0


def test_garch_arch_lm_and_multi_step_forecast_are_available(monkeypatch):
    dates = pd.date_range("2024-01-01", periods=180, freq="B")
    returns = pd.Series([0.01 if i % 2 == 0 else -0.008 for i in range(len(dates))], index=dates)
    close = 100 * (1 + returns).cumprod()

    class DummyMarketClient:
        def get_prices(self, ticker: str, start: str, end: str):
            return pd.DataFrame({"Close": close}, index=dates)

    service = GarchService(client=DummyMarketClient())
    result = service.analyze(
        ticker="TEST",
        start="2024-01-01",
        end="2024-12-31",
        return_type="simple",
        mode="estadistico",
        forecast_horizon=7,
    )

    assert "arch_lm_p_value" in result
    assert len(result["ewma_volatility"]) == result["observations"]
    assert result["ewma_latest_volatility"] == result["ewma_volatility"][-1]
    assert len(result["forecast"]) == 7
    assert all(point["step"] >= 1 for point in result["forecast"])


def test_fixed_income_treasury_curve_endpoint_returns_curve_points():
    response = client.get("/api/v1/fixed-income/treasury-curve")

    assert response.status_code == 200
    payload = response.json()

    assert "points" in payload
    assert len(payload["points"]) >= 4
    assert {"series_id", "maturity_years", "yield_rate"}.issubset(payload["points"][0])


def test_markowitz_frontier_is_qp_and_compares_non_negativity():
    dates = pd.date_range("2023-01-01", periods=260, freq="B")
    tickers = ["AAA", "BBB", "CCC", "DDD", "EEE"]

    class Settings:
        min_obs_portfolio = 60

    class DummyMarketClient:
        settings = Settings()

        def get_prices(self, ticker: str, start: str, end: str):
            idx = tickers.index(ticker)
            drift = 0.0002 + idx * 0.00005
            wave = pd.Series(
                [0.001 * ((i + idx) % 7 - 3) for i in range(len(dates))],
                index=dates,
            )
            close = 100 * (1 + drift + wave).cumprod()
            return pd.DataFrame({"Close": close}, index=dates)

    result = PortfolioService(client=DummyMarketClient()).build_efficient_frontier(
        tickers=tickers,
        start="2023-01-01",
        end="2024-01-01",
        rf_annual=0.04,
        n_portfolios=1000,
        return_type="simple",
    )

    comparison = result["short_selling_comparison"]

    assert result["frontier_method"] == "qp_target_return_grid"
    assert result["simulation_count"] == 1000
    assert len(result["simulated_portfolios"]) == 1000
    assert len(result["frontier"]) >= 3
    assert comparison["available"] is True
    assert len(comparison["restricted"]["frontier"]) >= 3
    assert len(comparison["with_short_selling"]["frontier"]) >= 3
    assert "zero_weight_assets" in comparison["restricted"]
    assert "cost_of_no_short_constraint" in comparison

    def assert_upper_frontier(points):
        ordered = sorted(points, key=lambda item: item["volatility"])
        returns = [item["return"] for item in ordered]
        assert all(next_ret >= current_ret - 1e-8 for current_ret, next_ret in zip(returns, returns[1:]))

    assert_upper_frontier(result["frontier"])
    assert_upper_frontier(comparison["restricted"]["frontier"])
    assert_upper_frontier(comparison["with_short_selling"]["frontier"])


def test_markowitz_min_variance_moves_away_from_equal_weights_when_risk_differs():
    service = PortfolioService(client=None)
    tickers = ["LOW", "MID", "HIGH"]
    mean_daily = pd.Series([0.0002, 0.00025, 0.0003], index=tickers)
    cov_daily = pd.DataFrame(
        np.diag([0.00002, 0.00020, 0.00080]),
        index=tickers,
        columns=tickers,
    )

    weights, metrics = service._optimize_min_variance(
        tickers=tickers,
        mean_daily=mean_daily,
        cov_daily=cov_daily,
        rf_annual=0.03,
        return_type="simple",
        allow_short_selling=False,
    )

    equal_weights = np.repeat(1.0 / len(tickers), len(tickers))
    equal_metrics = service._portfolio_metrics(
        weights=equal_weights,
        mean_daily=mean_daily,
        cov_daily=cov_daily,
        rf_annual=0.03,
        return_type="simple",
    )

    assert not np.allclose(weights, equal_weights, atol=1e-3)
    assert weights[0] > weights[1] > weights[2]
    assert metrics["volatility"] < equal_metrics["volatility"]


def test_saved_portfolio_endpoints_persist_user_portfolio_contract():
    payload = {
        "name": "pytest long-only portfolio",
        "owner": "pytest",
        "description": "Validacion rubrica persistencia",
        "tickers": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"],
        "weights_pct": [20, 20, 20, 20, 20],
        "horizon": "5y",
        "benchmark": {"ticker": "SPY", "name": "S&P 500 ETF"},
        "base_currency": "USD",
        "confidence_level": 0.95,
    }

    create_response = client.post("/api/v1/portfolio/saved", json=payload)

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["name"] == payload["name"]
    assert created["weights"]["tickers"] == payload["tickers"]
    assert sum(created["weights"]["weights_pct"]) == 100

    list_response = client.get("/api/v1/portfolio/saved", params={"owner": "pytest"})

    assert list_response.status_code == 200
    assert any(item["name"] == payload["name"] for item in list_response.json())


def test_alerts_module_uses_sma_cross_and_persists_triggered_signals():
    dates = pd.date_range("2024-01-01", periods=70, freq="B")
    close = pd.Series([100.0 - i * 0.3 for i in range(50)] + [85.0 + i * 2.0 for i in range(20)], index=dates)

    class DummyMarketClient:
        def get_prices(self, ticker: str, start: str, end: str):
            return pd.DataFrame({"Close": close, "High": close + 0.5, "Low": close - 0.5}, index=dates)

    service = AlertsService(client=DummyMarketClient())
    result = service.get_alerts(
        ticker="TEST",
        start="2024-01-01",
        end="2024-04-30",
        sma_short_window=5,
        sma_long_window=20,
    )

    moving_average = next(item for item in result["alerts"] if item["indicator"] == "MovingAverages")
    assert moving_average["rule"] == "sma_golden_death_cross"
    assert moving_average["signal"] in {"golden_cross", "death_cross", "sin_senal", "cercano_cruce_medias"}

    class DummyAlertsService:
        def get_alerts(self, **kwargs):
            return {
                "ticker": kwargs["ticker"],
                "start": kwargs["start"],
                "end": kwargs["end"],
                "alerts": [
                    {
                        "indicator": "RSI",
                        "rule": "rsi_extreme_zone",
                        "status": "alert",
                        "signal": "sobrecompra",
                        "severity": "media",
                        "value": 82.5,
                        "threshold_low": 30.0,
                        "threshold_high": 70.0,
                        "general_message": "RSI en zona extrema.",
                        "statistical_message": "RSI=82.50.",
                    }
                ],
                "total_alerts": 1,
            }

    app.dependency_overrides[get_alerts_service] = lambda: DummyAlertsService()
    before = client.get("/api/v1/persistence/health").json()["tables"]["signals_log"]
    response = client.get("/api/v1/alertas/TEST", params={"sma_short_window": 5, "sma_long_window": 20})
    app.dependency_overrides.pop(get_alerts_service, None)

    assert response.status_code == 200
    assert response.json()["alerts"][0]["rule"] == "rsi_extreme_zone"
    after = client.get("/api/v1/persistence/health").json()["tables"]["signals_log"]
    assert after >= before + 1


def test_ml_predict_persists_prediction_log_count():
    before = client.get("/api/v1/persistence/health").json()["tables"]["predictions_log"]

    response = client.post(
        "/api/v1/ml/predict",
        json={
            "ticker": "PORTFOLIO",
            "returns": [
                0.001,
                -0.002,
                0.003,
                0.0005,
                -0.001,
                0.002,
                0.0015,
                -0.0012,
                0.001,
                -0.002,
                0.003,
                0.0005,
                -0.095,
                0.002,
                0.0015,
                -0.0012,
                0.001,
                -0.002,
                0.003,
                0.0005,
            ],
        },
    )

    assert response.status_code == 200
    after = client.get("/api/v1/persistence/health").json()["tables"]["predictions_log"]
    assert after >= before + 1
