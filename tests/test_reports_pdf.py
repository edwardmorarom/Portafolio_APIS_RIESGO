from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


def test_custom_report_pdf_uses_dashboard_context():
    payload = {
        "portfolio_context": {
            "tickers": "AAPL, MSFT, NVDA, AMZN, JPM",
            "weights": "20%, 20%, 20%, 20%, 20%",
            "horizon": "1 año",
            "benchmark": "SPY",
        },
        "benchmark_context": {
            "ticker": "SPY",
            "reason": "Todos los activos son de Estados Unidos.",
        },
        "key_results": {
            "var_cvar_kupiec": "VaR y Kupiec calculados desde el módulo 5.",
        },
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/reports/executive-summary/pdf", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_report_summary_keeps_rubric_sections_to_five_pages_scope():
    with TestClient(app) as client:
        response = client.get("/api/v1/reports/executive-summary")

    assert response.status_code == 200
    payload = response.json()
    sections = payload["sections"]

    assert len(sections) == 5
    assert "Riesgo financiero" in sections[0]["title"]
    assert "Decisiones metodológicas" in sections[1]["title"]
    assert "Arquitectura técnica" in sections[2]["title"]
    assert "Resultados numéricos clave" in sections[3]["title"]
    assert "Conclusiones" in sections[4]["title"]
