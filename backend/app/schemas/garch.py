from pydantic import BaseModel, Field, field_validator


class GarchRequest(BaseModel):
    ticker: str = Field(..., description="Ticker del activo")
    start: str = Field(default="2021-01-01", description="Fecha inicial")
    end: str = Field(default="2026-12-31", description="Fecha final")
    return_type: str = Field(default="log", description="simple o log")
    mode: str = Field(default="estadistico", description="general o estadistico")
    forecast_horizon: int = Field(default=5, ge=1, le=30, description="Horizonte de pronostico")

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        value = v.strip().upper()
        if not value:
            raise ValueError("ticker no puede ser vacio")
        return value

    @field_validator("return_type")
    @classmethod
    def validate_return_type(cls, v: str) -> str:
        value = v.strip().lower()
        if value not in {"simple", "log"}:
            raise ValueError("return_type debe ser 'simple' o 'log'")
        return value

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        value = v.strip().lower()
        if value not in {"general", "estadistico"}:
            raise ValueError("mode debe ser 'general' o 'estadistico'")
        return value


class GarchModelResult(BaseModel):
    model_name: str
    log_likelihood: float
    aic: float
    bic: float


class GarchForecastPoint(BaseModel):
    step: int
    variance: float
    volatility: float


class GarchResponse(BaseModel):
    ticker: str
    start: str
    end: str
    return_type: str
    observations: int
    candidate_models: list[GarchModelResult] = Field(default_factory=list)
    best_model: str
    best_model_aic: float
    best_model_bic: float
    residuals_jarque_bera_stat: float
    residuals_jarque_bera_p_value: float
    residuals_normality_conclusion: str
    conditional_volatility: list[float] = Field(default_factory=list)
    forecast: list[GarchForecastPoint] = Field(default_factory=list)
    effective_forecast_horizon: int
    mode: str
    summary: str