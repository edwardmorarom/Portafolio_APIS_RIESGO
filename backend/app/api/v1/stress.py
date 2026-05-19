from fastapi import APIRouter, Depends

from app.schemas.stress import StressScenarioRequest, StressScenarioResponse
from app.services.stress_service import StressTestingService


router = APIRouter()


def get_stress_service() -> StressTestingService:
    return StressTestingService()


@router.post("/scenario", response_model=StressScenarioResponse)
def run_stress_scenario(
    request: StressScenarioRequest,
    service: StressTestingService = Depends(get_stress_service),
):
    return service.run_scenario(
        portfolio_value=request.portfolio_value,
        expected_return=request.expected_return,
        volatility=request.volatility,
        var_95=request.var_95,
        beta=request.beta,
        rate_shock=request.rate_shock,
        market_shock=request.market_shock,
        volatility_multiplier=request.volatility_multiplier,
    )
