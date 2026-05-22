from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.fixed_income import BondPurchaseRequest, BondPurchaseResponse
from app.services.yield_service import YieldService


router = APIRouter()


def get_yield_service() -> YieldService:
    return YieldService()


@router.post(
    "/bond/purchase",
    response_model=BondPurchaseResponse,
    summary="Simulador de compra de bono TES",
)
async def simulate_bond_purchase(
    request: BondPurchaseRequest,
    service: YieldService = Depends(get_yield_service),
):
    try:
        return service.calculate_bond_purchase(request=request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error simulando compra de bono: {exc}")
