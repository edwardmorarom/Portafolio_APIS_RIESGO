from fastapi import APIRouter, Depends

from app.core.dependencies import get_investor_service
from app.schemas.investor import (
    InvestorPreferencesRequest,
    InvestorPreferencesResponse,
    KYCProfileRequest,
    KYCProfileResponse,
)
from app.services.investor_service import InvestorService


router = APIRouter()


@router.post(
    "/preferences",
    summary="Validar preferencias del inversionista",
    response_model=InvestorPreferencesResponse,
)
async def validate_preferences(
    payload: InvestorPreferencesRequest,
    service: InvestorService = Depends(get_investor_service),
) -> InvestorPreferencesResponse:
    result = service.resolve_horizon(payload)
    return InvestorPreferencesResponse(**result)


@router.post(
    "/kyc/profile",
    summary="Calcular perfil de riesgo sugerido por KYC",
    response_model=KYCProfileResponse,
)
async def suggest_kyc_profile(
    payload: KYCProfileRequest,
    service: InvestorService = Depends(get_investor_service),
) -> KYCProfileResponse:
    result = service.suggest_profile(
        age=payload.age,
        experience=payload.experience,
        tolerance=payload.tolerance,
    )
    return KYCProfileResponse(**result)
