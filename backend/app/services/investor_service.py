from __future__ import annotations
from datetime import date, timedelta
from app.schemas.investor import InvestorPreferencesRequest

class InvestorService:
    def determine_risk_profile(self, kyc_answers: dict) -> str:
        """
        Motor de Reglas USTA: Calcula el perfil basado en scoring.
        kyc_answers: {'age': int, 'experience': int, 'tolerance': int}
        """
        score = 0
        
        # Regla 1: Edad (Inversa al riesgo)
        age = kyc_answers.get("age", 40)
        if age < 30: score += 3
        elif age < 50: score += 2
        else: score += 1
        
        # Regla 2: Experiencia (0-5 años)
        exp = kyc_answers.get("experience", 0)
        if exp >= 5: score += 3
        elif exp >= 2: score += 2
        else: score += 1
        
        # Regla 3: Tolerancia subjetiva (1-5)
        tol = kyc_answers.get("tolerance", 1)
        score += tol # Suma directa del 1 al 5

        # Mapeo de resultados
        if score >= 9: return "agresivo"
        if score >= 6: return "moderado"
        return "conservador"

    def resolve_horizon(self, payload: InvestorPreferencesRequest) -> dict:
        today = date.today()
        # Lógica de horizontes (1y, 3y, 5y) ya implementada
        if payload.horizon_type == "1y":
            start = today - timedelta(days=365)
            end = today
        elif payload.horizon_type == "3y":
            start = today - timedelta(days=365 * 3)
            end = today
        else:
            start = today - timedelta(days=365 * 5)
            end = today
            
        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "risk_profile": payload.risk_profile,
            "message": "Preferencias validadas exitosamente"
        }
