from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


client = TestClient(app)


def _tes_payload() -> dict:
    return {
        "issue_date": "2019-10-08",
        "maturity_date": "2034-10-18",
        "settlement_date": "2026-05-21",
        "face_value": 1_000_000_000.0,
        "coupon_rate": 0.0725,
        "coupon_rate_type": "nominal_anual",
        "coupon_frequency": 1,
        "market_yield": 0.0957,
        "market_yield_type": "nominal_anual",
        "clean_price_pct": 95.50,
        "fees_pct": 0.25,
        "fixed_fee": 0.0,
        "currency": "COP",
    }


def test_bond_purchase_tes_like_excel_returns_cashflows_and_interpretation():
    response = client.post("/api/v1/fixed-income/bond/purchase", json=_tes_payload())

    assert response.status_code == 200
    data = response.json()

    assert data["position"] == "purchase"
    assert data["cashflows"]
    assert data["interpretation"]
    assert data["rates"]["coupon_periodic_rate"] > 0
    assert data["rates"]["market_yield_periodic"] > 0


def test_bond_purchase_rejects_invalid_dates():
    payload = _tes_payload()
    payload["settlement_date"] = "2035-01-01"

    response = client.post("/api/v1/fixed-income/bond/purchase", json=payload)

    assert response.status_code == 422


def test_bond_purchase_rejects_negative_nominal():
    payload = _tes_payload()
    payload["face_value"] = -100.0

    response = client.post("/api/v1/fixed-income/bond/purchase", json=payload)

    assert response.status_code == 422


def test_bond_purchase_rejects_non_positive_clean_price():
    payload = _tes_payload()
    payload["clean_price_pct"] = 0.0

    response = client.post("/api/v1/fixed-income/bond/purchase", json=payload)

    assert response.status_code == 422


def test_bond_purchase_totals_match_price_formulas():
    response = client.post("/api/v1/fixed-income/bond/purchase", json=_tes_payload())

    assert response.status_code == 200
    metrics = response.json()["metrics"]

    assert metrics["dirty_price"] == metrics["clean_price_value"] + metrics["accrued_interest"]
    assert metrics["total_purchase"] == metrics["dirty_price"] + metrics["fees"]


def test_bond_purchase_last_cashflow_includes_coupon_and_nominal():
    payload = _tes_payload()
    response = client.post("/api/v1/fixed-income/bond/purchase", json=payload)

    assert response.status_code == 200
    data = response.json()
    last_cashflow = data["cashflows"][-1]
    coupon = data["metrics"]["coupon_per_period"]

    assert last_cashflow["payment_date"] == payload["maturity_date"]
    assert last_cashflow["cashflow"] == coupon + payload["face_value"]


def test_bond_purchase_duration_and_dv01_are_positive():
    response = client.post("/api/v1/fixed-income/bond/purchase", json=_tes_payload())

    assert response.status_code == 200
    metrics = response.json()["metrics"]

    assert metrics["modified_duration"] > 0
    assert metrics["dv01"] > 0
