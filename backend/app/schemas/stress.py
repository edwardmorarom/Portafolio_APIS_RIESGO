from __future__ import annotations

from pydantic import BaseModel, Field


class StressScenarioRequest(BaseModel):
    portfolio_value: float = Field(..., gt=0)
    expected_return: float
    volatility: float = Field(..., gt=0)
    var_95: float
    beta: float
    rate_shock: float = 0.0
    market_shock: float = 0.0
    benchmark_shock: float | None = None
    volatility_multiplier: float = Field(1.0, gt=0)


class StressScenarioResponse(BaseModel):
    base_portfolio_value: float
    stressed_return: float
    stressed_volatility: float
    stressed_var_95: float
    estimated_loss_pct: float
    estimated_loss: float
    stressed_portfolio_value: float
    benchmark_loss_pct: float | None = None
    relative_to_benchmark: str | None = None
    severity: str
    interpretation: str
    summary: str
