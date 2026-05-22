from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator


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


class StressPortfolioAsset(BaseModel):
    ticker: str = Field(..., min_length=1)
    weight: float = Field(..., ge=0, description="Peso decimal del activo dentro del portafolio")
    beta: float = Field(default=1.0, description="Beta del activo frente al benchmark")
    duration: float | None = Field(default=None, ge=0, description="Duracion aproximada si el activo es renta fija")
    convexity: float | None = Field(default=None, ge=0, description="Convexidad aproximada si el activo es renta fija")

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()


class StressScenarioSpec(BaseModel):
    name: str = Field(..., min_length=1)
    rate_shock_bp: int = 0
    market_drop_pct: float = 0.0
    vol_multiplier: float = Field(1.0, gt=0)


class StressTestRequest(BaseModel):
    portfolio_value: float = Field(..., gt=0)
    portfolio: list[StressPortfolioAsset] = Field(..., min_length=1)
    scenarios: list[StressScenarioSpec] = Field(..., min_length=1)
    expected_return: float = 0.0
    volatility: float = Field(..., gt=0)
    var_parametric_99: float | None = None
    var_monte_carlo_99: float | None = None

    @model_validator(mode="after")
    def validate_weights(self):
        total = sum(asset.weight for asset in self.portfolio)
        if total <= 0:
            raise ValueError("La suma de pesos debe ser mayor que 0")
        return self


class StressBaseMetrics(BaseModel):
    portfolio_value: float
    expected_return: float
    volatility: float
    var_parametric_99: float
    var_monte_carlo_99: float


class StressAssetImpact(BaseModel):
    ticker: str
    weight: float
    beta: float
    price_change_pct: float
    contribution_pct: float


class StressScenarioMetrics(BaseModel):
    scenario_name: str
    loss_pct: float
    loss_amount: float
    stressed_portfolio_value: float
    stressed_volatility: float
    stressed_var_parametric_99: float
    stressed_var_monte_carlo_99: float
    severity: str
    asset_impacts: list[StressAssetImpact]
    interpretation: str


class StressTestResponse(BaseModel):
    base_metrics: StressBaseMetrics
    stressed_metrics: list[StressScenarioMetrics]
