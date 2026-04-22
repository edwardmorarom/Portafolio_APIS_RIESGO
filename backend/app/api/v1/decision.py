from fastapi import APIRouter

from app.schemas.decision import DecisionRouterResponse

router = APIRouter()


@router.get("/", summary="Router decision base", response_model=DecisionRouterResponse)
async def decision_root() -> DecisionRouterResponse:
    return DecisionRouterResponse(message="Decision router active")