from fastapi import APIRouter, Depends

from app.core.dependencies import get_investor_service
from app.schemas.investor import InvestorPreferencesRequest, InvestorPreferencesResponse
from app.services.investor_service import InvestorService

router = APIRouter()


@router.post("/preferences", summary="Validar preferencias del inversionista", response_model=InvestorPreferencesResponse)
async def validate_preferences(
    payload: InvestorPreferencesRequest,
    service: InvestorService = Depends(get_investor_service),
) -> InvestorPreferencesResponse:
    result = service.resolve_horizon(payload)
    return InvestorPreferencesResponse(**result)