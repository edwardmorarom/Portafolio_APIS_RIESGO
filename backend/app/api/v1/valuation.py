from fastapi import APIRouter, Depends, HTTPException

from app.schemas.valuation import (
    BondMetricsRequest,
    BondMetricsResponse,
    OptionPricingRequest,
    OptionPricingResponse,
    OptionValuationRequest,
    OptionValuationResponse,
    YieldCurveRequest,
    YieldCurveResponse,
)
from app.services.option_service import OptionService
from app.services.yield_service import YieldService


router = APIRouter()


def get_yield_service() -> YieldService:
    return YieldService()


def get_option_service() -> OptionService:
    return OptionService()


@router.post(
    "/nelson-siegel",
    response_model=YieldCurveResponse,
    summary="Ajuste de curva Nelson-Siegel",
)
async def fit_nelson_siegel(
    request: YieldCurveRequest,
    service: YieldService = Depends(get_yield_service),
):
    if len(request.yields) != len(request.maturities):
        raise HTTPException(
            status_code=400,
            detail="Las listas de tasas y plazos deben tener la misma longitud.",
        )

    try:
        return service.fit_nelson_siegel(request.yields, request.maturities)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al ajustar Nelson-Siegel: {str(e)}",
        )


@router.post(
    "/bond-metrics",
    response_model=BondMetricsResponse,
    summary="Metricas de renta fija",
)
async def calculate_bond_metrics(
    request: BondMetricsRequest,
    service: YieldService = Depends(get_yield_service),
):
    try:
        return service.calculate_bond_metrics(
            face_value=request.face_value,
            coupon_rate=request.coupon_rate,
            maturity_years=request.maturity_years,
            market_yield=request.market_yield,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en metricas de renta fija: {str(e)}",
        )


@router.post(
    "/black-scholes",
    response_model=OptionValuationResponse,
    summary="Valoracion de opciones Black-Scholes",
)
async def calculate_option(
    request: OptionValuationRequest,
    service: OptionService = Depends(get_option_service),
):
    try:
        result = service.calculate_black_scholes(
            S=request.spot_price,
            K=request.strike_price,
            T=request.time_to_maturity,
            r=request.risk_free_rate,
            sigma=request.volatility,
            option_type=request.option_type,
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en el motor de valoracion: {str(e)}",
        )


@router.post(
    "/precio",
    response_model=OptionPricingResponse,
    summary="Precio de opcion europea con Black-Scholes",
)
async def price_option(
    request: OptionPricingRequest,
    service: OptionService = Depends(get_option_service),
):
    try:
        result = service.calculate_black_scholes(
            S=request.S,
            K=request.K,
            T=request.T,
            r=request.r,
            sigma=request.sigma,
            option_type=request.tipo,
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en el motor de valoracion: {str(e)}",
        )
