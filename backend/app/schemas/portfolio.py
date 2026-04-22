from pydantic import BaseModel, Field, field_validator


class EfficientFrontierRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=2, description="Tickers del portafolio")
    start: str = Field(default="2021-01-01", description="Fecha inicial")
    end: str = Field(default="2026-12-31", description="Fecha final")
    rf_annual: float = Field(default=0.04, ge=0.0, le=1.0, description="Tasa libre de riesgo anual")
    n_portfolios: int = Field(default=5000, ge=1000, le=50000, description="Número de portafolios simulados")
    return_type: str = Field(default="log", description="Tipo de rendimiento: simple o log")

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: list[str]) -> list[str]:
        cleaned = [item.strip().upper() for item in v if item.strip()]
        if len(cleaned) < 2:
            raise ValueError("Debe enviar al menos dos tickers válidos")
        return cleaned

    @field_validator("return_type")
    @classmethod
    def validate_return_type(cls, v: str) -> str:
        value = v.strip().lower()
        if value not in {"simple", "log"}:
            raise ValueError("return_type debe ser 'simple' o 'log'")
        return value


class FrontierPoint(BaseModel):
    volatility: float = Field(..., description="Volatilidad anualizada")
    return_: float = Field(..., alias="return", description="Retorno anualizado")


class PortfolioWeightsItem(BaseModel):
    asset: str = Field(..., description="Ticker del activo")
    weight: float = Field(..., description="Peso del activo")


class OptimalPortfolio(BaseModel):
    return_: float = Field(..., alias="return", description="Retorno anualizado")
    volatility: float = Field(..., description="Volatilidad anualizada")
    sharpe: float = Field(..., description="Ratio de Sharpe")
    weights: list[PortfolioWeightsItem] = Field(default_factory=list, description="Composición del portafolio")


class EfficientFrontierResponse(BaseModel):
    tickers: list[str] = Field(..., description="Tickers analizados")
    start: str = Field(..., description="Fecha inicial")
    end: str = Field(..., description="Fecha final")
    rf_annual: float = Field(..., description="Tasa libre de riesgo anual")
    frontier: list[FrontierPoint] = Field(default_factory=list, description="Puntos de la frontera eficiente")
    min_variance: OptimalPortfolio = Field(..., description="Portafolio de mínima varianza")
    max_sharpe: OptimalPortfolio = Field(..., description="Portafolio de máximo Sharpe")