from __future__ import annotations

from datetime import date, timedelta

from app.schemas.investor import InvestorPreferencesRequest


class InvestorService:
    def resolve_horizon(self, payload: InvestorPreferencesRequest) -> dict:
        today = date.today()

        if payload.horizon_type == "1y":
            start = today - timedelta(days=365)
            end = today
        elif payload.horizon_type == "3y":
            start = today - timedelta(days=365 * 3)
            end = today
        elif payload.horizon_type == "5y":
            start = today - timedelta(days=365 * 5)
            end = today
        else:
            start = date.fromisoformat(payload.start)
            end = date.fromisoformat(payload.end)

        if payload.risk_profile == "cero_riesgo":
            message = "Si el inversor desea 0 riesgo, no debería invertir en renta variable."
        else:
            message = "Preferencias del inversionista validadas correctamente."

        return {
            "tickers": payload.tickers,
            "weights_pct": payload.weights_pct,
            "weights_decimal": [w / 100.0 for w in payload.weights_pct],
            "base_currency": payload.base_currency,
            "confidence_level": payload.confidence_level,
            "risk_profile": payload.risk_profile,
            "horizon_type": payload.horizon_type,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "return_type": payload.return_type,
            "mode": payload.mode,
            "target_return_annual": payload.target_return_annual,
            "message": message,
        }