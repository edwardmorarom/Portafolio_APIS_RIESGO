from pydantic import BaseModel, Field


class MLPredictionRequest(BaseModel):
    volatility: float = Field(..., gt=0)
    sharpe_ratio: float
    var_95: float
    beta: float
    market_return: float
    horizon_months: int = Field(default=12, ge=1, le=60)
    model_name: str = Field(default="gradient_boosting")


class MLPredictionResponse(BaseModel):
    predicted_return: float
    model_predictions: dict[str, float]
    horizon_months: int
    model_version: str
    model_type: str = "Ridge/Lasso/GradientBoostingRegressor"
    target: str = "Predicción de retorno acumulado a horizonte fijo"
    interpretation: str
