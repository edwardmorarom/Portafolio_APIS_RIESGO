from __future__ import annotations

from app.clients.macro_client import MacroClient


class MacroService:
    def __init__(self, client: MacroClient) -> None:
        self.client = client

    def get_macro_snapshot(self, base_currency: str) -> dict:
        return self.client.get_macro_snapshot(base_currency=base_currency)

    def resolve_rf_inputs(self, base_currency: str) -> tuple[str, float]:
        snapshot = self.get_macro_snapshot(base_currency=base_currency)
        rf_ticker = snapshot["rf_ticker"]
        rf_pct = snapshot["risk_free_rate_pct"] if snapshot["risk_free_rate_pct"] is not None else 0.0
        return rf_ticker, float(rf_pct)