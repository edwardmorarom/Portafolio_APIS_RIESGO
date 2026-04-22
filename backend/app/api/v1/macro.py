from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_macro_service
from app.schemas.macro import MacroSnapshotResponse
from app.services.macro_service import MacroService
from app.schemas.macro import FxSpotResponse

router = APIRouter()


@router.get("/", summary="Snapshot macroeconómico", response_model=MacroSnapshotResponse)
async def get_macro_snapshot(
    base_currency: str = Query(default="USD"),
    service: MacroService = Depends(get_macro_service),
) -> MacroSnapshotResponse:
    try:
        data = service.get_macro_snapshot(base_currency=base_currency)
        return MacroSnapshotResponse(**data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fx-spot/{base_currency}", summary="Spot FX y referencia macro por moneda base", response_model=FxSpotResponse)
async def get_fx_spot(
    base_currency: str,
    service: MacroService = Depends(get_macro_service),
) -> FxSpotResponse:
    try:
        result = service.get_fx_spot(base_currency=base_currency)
        return FxSpotResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc