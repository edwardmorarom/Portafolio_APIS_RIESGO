from fastapi import APIRouter, Depends, HTTPException
from app.schemas.valuation import YieldCurveRequest, YieldCurveResponse, OptionValuationRequest, OptionValuationResponse
from app.services.yield_service import YieldService
from app.services.option_service import OptionService

router = APIRouter()

# Inyección de dependencias (para instanciar los servicios de forma limpia)
def get_yield_service() -> YieldService:
    return YieldService()

def get_option_service() -> OptionService:
    return OptionService()

@router.post("/nelson-siegel", response_model=YieldCurveResponse, summary="Ajuste de curva Nelson-Siegel")
async def fit_nelson_siegel(
    request: YieldCurveRequest,
    service: YieldService = Depends(get_yield_service)
):
    """
    Recibe un vector de tasas y vencimientos, y devuelve los parámetros beta
    ajustados mediante el modelo de Nelson-Siegel.
    """
    if len(request.yields) != len(request.maturities):
        raise HTTPException(status_code=400, detail="Las listas de tasas y plazos deben tener la misma longitud.")
    
    try:
        result = service.fit_nelson_siegel(request.yields, request.maturities)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ajustar Nelson-Siegel: {str(e)}")

@router.post("/black-scholes", response_model=OptionValuationResponse, summary="Valoración de opciones Black-Scholes")
async def calculate_option(
    request: OptionValuationRequest,
    service: OptionService = Depends(get_option_service)
):
    """
    Valora una opción (Call/Put) usando Black-Scholes y devuelve su precio y letras griegas.
    """
    try:
        result = service.calculate_black_scholes(
            S=request.spot_price,
            K=request.strike_price,
            T=request.time_to_maturity,
            r=request.risk_free_rate,
            sigma=request.volatility,
            option_type=request.option_type
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el motor de valoración: {str(e)}")