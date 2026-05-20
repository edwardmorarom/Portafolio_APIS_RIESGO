from __future__ import annotations

from datetime import date, timedelta

from app.schemas.investor import InvestorPreferencesRequest


class InvestorService:
    def calculate_kyc_score(self, age: int, experience: int, tolerance: int) -> int:
        score = 0

        if age < 30:
            score += 3
        elif age < 50:
            score += 2
        else:
            score += 1

        if experience >= 5:
            score += 3
        elif experience >= 2:
            score += 2
        else:
            score += 1

        score += tolerance

        return score

    def determine_risk_profile(self, kyc_answers: dict) -> str:
        score = self.calculate_kyc_score(
            age=int(kyc_answers.get("age", 40)),
            experience=int(kyc_answers.get("experience", 0)),
            tolerance=int(kyc_answers.get("tolerance", 1)),
        )

        if score >= 9:
            return "agresivo"
        if score >= 6:
            return "moderado"
        return "conservador"

    def suggest_profile(self, age: int, experience: int, tolerance: int) -> dict:
        score = self.calculate_kyc_score(
            age=age,
            experience=experience,
            tolerance=tolerance,
        )

        if score >= 9:
            profile = "agresivo"
            explanation = (
                "Perfil agresivo sugerido: el inversionista muestra mayor tolerancia "
                "al riesgo, mayor horizonte potencial o experiencia suficiente para "
                "asumir volatilidad."
            )
        elif score >= 6:
            profile = "moderado"
            explanation = (
                "Perfil moderado sugerido: el inversionista puede asumir riesgo "
                "intermedio, balanceando crecimiento y control de volatilidad."
            )
        else:
            profile = "conservador"
            explanation = (
                "Perfil conservador sugerido: se recomienda priorizar preservacion "
                "de capital y menor exposicion a volatilidad."
            )

        return {
            "suggested_profile": profile,
            "score": score,
            "explanation": explanation,
        }

    def resolve_horizon(self, payload: InvestorPreferencesRequest) -> dict:
        today = date.today()

        if payload.horizon_type == "1y":
            start = today - timedelta(days=365)
            end = today
        elif payload.horizon_type == "2y":
            start = today - timedelta(days=365 * 2)
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

        weights_decimal = [w / 100 for w in payload.weights_pct]

        return {
            "tickers": payload.tickers,
            "weights_pct": payload.weights_pct,
            "weights_decimal": weights_decimal,
            "base_currency": payload.base_currency,
            "confidence_level": payload.confidence_level,
            "risk_profile": payload.risk_profile,
            "horizon_type": payload.horizon_type,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "return_type": payload.return_type,
            "mode": payload.mode,
            "target_return_annual": payload.target_return_annual,
            "message": "Preferencias validadas exitosamente",
        }
