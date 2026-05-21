from pydantic import BaseModel, Field


class MLPredictionRequest(BaseModel):
    volatility: float = Field(..., gt=0)
    sharpe_ratio: float
    var_95: float
    beta: float
    market_return: float


class MLPredictionResponse(BaseModel):
    predicted_return: float
    model_version: str
    model_type: str = "LinearRegression"
    target: str = "Retorno esperado del portafolio"
    interpretation: str
