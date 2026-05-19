from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.portfolio_service import PortfolioService  # noqa: E402


def test_portfolio_service_builds_perri_comparison_for_exact_size():
    service = PortfolioService(client=None)

    result = service._build_perri_comparison(
        portfolio_size=5,
        start="2021-01-01",
        end="2026-01-01",
        min_variance_payload={
            "return": 0.08,
            "volatility": 0.12,
            "sharpe": 0.40,
        },
        max_sharpe_payload={
            "return": 0.14,
            "volatility": 0.18,
            "sharpe": 0.56,
        },
        max_return_payload={
            "return": 0.20,
            "volatility": 0.30,
            "sharpe": 0.53,
        },
    )

    assert result["enabled"] is True
    assert result["portfolio_size"] == 5
    assert result["horizon"] == "5y"
    assert result["message"] == "Comparación contra umbrales institucionales Perri generada correctamente."

    objectives = {item["objective"] for item in result["comparisons"]}

    assert objectives == {"min_risk", "max_sharpe", "max_return"}

    for item in result["comparisons"]:
        assert item["perri_return"] is not None
        assert item["perri_volatility"] is not None
        assert item["perri_sharpe"] is not None
        assert item["verdict"]


def test_portfolio_service_disables_perri_comparison_for_non_exact_size():
    service = PortfolioService(client=None)

    result = service._build_perri_comparison(
        portfolio_size=7,
        start="2021-01-01",
        end="2026-01-01",
        min_variance_payload={
            "return": 0.08,
            "volatility": 0.12,
            "sharpe": 0.40,
        },
        max_sharpe_payload={
            "return": 0.14,
            "volatility": 0.18,
            "sharpe": 0.56,
        },
        max_return_payload={
            "return": 0.20,
            "volatility": 0.30,
            "sharpe": 0.53,
        },
    )

    assert result["enabled"] is False
    assert result["portfolio_size"] == 7
    assert result["horizon"] == "5y"
    assert result["comparisons"] == []
    assert "5, 10 o 15 activos" in result["message"]
