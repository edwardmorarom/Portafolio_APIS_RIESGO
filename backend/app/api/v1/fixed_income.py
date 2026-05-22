from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.clients.macro_client import MacroClient
from app.core.dependencies import get_macro_client
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


@router.get("/treasury-curve", summary="Curva Treasury desde FRED para Nelson-Siegel")
async def get_treasury_curve(
    client: MacroClient = Depends(get_macro_client),
) -> dict:
    return client.get_us_treasury_yield_curve()
