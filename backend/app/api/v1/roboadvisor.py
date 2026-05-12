from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.clients.market_client import MarketClient
from app.core.dependencies import get_market_client
from app.services.roboadvisor_service import RoboAdvisorService

router = APIRouter()

# --- ESQUEMA DE ENTRADA (CONTRATO) ---
class RoboAdvisorRequest(BaseModel):
    profile: str = Field(..., description="Perfil de riesgo: conservador, moderado, agresivo")
    total_assets: int = Field(..., ge=2, le=15, description="Cantidad total de activos en el portafolio")
    custom_tickers: list[str] = Field(default_factory=list, description="Activos que el usuario exige tener (caprichos)")

# --- INYECCIÓN DE DEPENDENCIA ---
def get_roboadvisor_service(market_client: MarketClient = Depends(get_market_client)) -> RoboAdvisorService:
    return RoboAdvisorService(market_client=market_client)

# --- ENDPOINT ---
@router.post("/suggest", summary="Generar Portafolio Híbrido Institucional")
async def suggest_portfolio(
    payload: RoboAdvisorRequest,
    service: RoboAdvisorService = Depends(get_roboadvisor_service)
):
    """
    Toma los 'caprichos' del usuario, los mezcla con los mejores activos de la reserva
    según el perfil de riesgo, y optimiza los pesos usando el modelo de Markowitz.
    """
    try:
        result = service.suggest_hybrid_portfolio(
            profile=payload.profile,
            total_assets=payload.total_assets,
            custom_tickers=payload.custom_tickers
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))