from __future__ import annotations

from app.clients.macro_client import MacroClient
from app.clients.market_client import MarketClient
from datetime import date


class MacroService:
    def __init__(self, client: MacroClient, market_client: MarketClient) -> None:
        self.client = client
        self.market_client = market_client

    def get_macro_snapshot(self, base_currency: str) -> dict:
        return self.client.get_macro_snapshot(base_currency=base_currency)

    def resolve_rf_inputs(self, base_currency: str) -> tuple[str, float]:
        snapshot = self.get_macro_snapshot(base_currency=base_currency)
        rf_ticker = snapshot["rf_ticker"]
        rf_pct = snapshot["risk_free_rate_pct"] if snapshot["risk_free_rate_pct"] is not None else 0.0
        return rf_ticker, float(rf_pct)

    def get_fx_spot(self, base_currency: str) -> dict:
        base_currency = base_currency.strip().upper()

        fx_map = {
            "USD": {"fx_ticker": "USDCOP=X", "quote_currency": "COP"},
            "EUR": {"fx_ticker": "EURCOP=X", "quote_currency": "COP"},
            "COP": {"fx_ticker": "USDCOP=X", "quote_currency": "COP"},
        }

        if base_currency not in fx_map:
            raise ValueError("base_currency debe ser USD, EUR o COP")

        selected = fx_map[base_currency]
        fx_ticker = selected["fx_ticker"]
        quote_currency = selected["quote_currency"]

        today = date.today().isoformat()

        df = self.market_client.get_prices(
            ticker=fx_ticker,
            start="2025-01-01",
            end=today,
        )

        if df.empty or "Close" not in df.columns:
            raise ValueError(f"No fue posible obtener spot FX para {fx_ticker}")

        close = df["Close"].dropna()
        if close.empty:
            raise ValueError(f"No fue posible obtener spot FX para {fx_ticker}")

        spot = float(close.iloc[-1])
        spot_date = str(close.index[-1].date())

        rf_ticker, rf_rate_pct = self.resolve_rf_inputs(base_currency=base_currency)

        if base_currency == "COP":
            message = (
                f"Moneda base COP. Se usa spot {fx_ticker}={spot:.4f} "
                f"y la tasa libre de riesgo se aproxima con {rf_ticker}."
            )
        else:
            message = (
                f"Moneda base {base_currency}. Spot actual {fx_ticker}={spot:.4f}. "
                f"Benchmark por defecto ACWI y Rf desde {rf_ticker}."
            )

        return {
            "base_currency": base_currency,
            "quote_currency": quote_currency,
            "fx_ticker": fx_ticker,
            "spot": spot,
            "spot_date": spot_date,
            "rf_ticker": rf_ticker,
            "rf_rate_pct": rf_rate_pct,
            "benchmark_ticker": "ACWI",
            "message": message,
        }