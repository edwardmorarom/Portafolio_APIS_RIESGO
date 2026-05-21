from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

from ui.benchmarking import resolve_benchmark  # noqa: E402


def test_resolve_benchmark_uses_spy_for_us_only_portfolio():
    assets = [
        {"ticker": "AAPL", "name": "Apple", "country": "US"},
        {"ticker": "MSFT", "name": "Microsoft", "country": "United States"},
    ]

    benchmark = resolve_benchmark(assets)

    assert benchmark["ticker"] == "SPY"
    assert benchmark["criterion"] == "us_only"


def test_resolve_benchmark_uses_acwi_for_international_portfolio():
    assets = [
        {"ticker": "AAPL", "name": "Apple", "country": "US"},
        {"ticker": "3382.T", "name": "Seven & i Holdings", "country": "JP"},
    ]

    benchmark = resolve_benchmark(assets)

    assert benchmark["ticker"] == "ACWI"
    assert benchmark["criterion"] == "global_or_mixed"
