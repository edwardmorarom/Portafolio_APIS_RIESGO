from fastapi import APIRouter, Depends

from app.schemas.stress import (
    StressScenarioRequest,
    StressScenarioResponse,
    StressTestRequest,
    StressTestResponse,
)
from app.services.stress_service import StressTestingService


router = APIRouter()


def get_stress_service() -> StressTestingService:
    return StressTestingService()


@router.post("", response_model=StressTestResponse)
@router.post("/", response_model=StressTestResponse)
def run_stress_test(
    request: StressTestRequest,
    service: StressTestingService = Depends(get_stress_service),
):
    return service.run_stress_test(
        portfolio_value=request.portfolio_value,
        portfolio=[asset.model_dump() for asset in request.portfolio],
        scenarios=[scenario.model_dump() for scenario in request.scenarios],
        expected_return=request.expected_return,
        volatility=request.volatility,
        var_parametric_99=request.var_parametric_99,
        var_monte_carlo_99=request.var_monte_carlo_99,
    )


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
        benchmark_shock=request.benchmark_shock,
        volatility_multiplier=request.volatility_multiplier,
    )
