from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class GarchRequest(BaseModel):
    ticker: str = Field(..., description="Ticker del activo")
    start: str = Field(default="2021-01-01", description="Fecha inicial")
    end: str = Field(default="2026-12-31", description="Fecha final")
    return_type: str = Field(default="log", description="simple o log")
    mode: str = Field(default="estadistico", description="general o estadistico")
    forecast_horizon: int = Field(default=5, ge=1, le=30, description="Horizonte de pronostico")
    distribution: str = Field(default="normal", description="Distribución de errores: normal o t")
    ewma_lambda: float = Field(default=0.94, ge=0.70, le=0.99, description="Factor lambda EWMA")

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

    @field_validator("distribution")
    @classmethod
    def validate_distribution(cls, v: str) -> str:
        value = v.strip().lower()
        if value in {"student", "student-t", "t-student", "t_student"}:
            value = "t"
        if value not in {"normal", "t"}:
            raise ValueError("distribution debe ser 'normal' o 't'")
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

    distribution: str = Field(default="normal", description="Distribución de errores seleccionada")
    distribution_label: str = Field(default="Normal", description="Etiqueta legible de distribución")

    candidate_models: list[GarchModelResult] = Field(default_factory=list)

    best_model: str
    best_model_aic: float
    best_model_bic: float

    residuals_jarque_bera_stat: float
    residuals_jarque_bera_p_value: float
    residuals_normality_conclusion: str
    arch_lm_lags: int = Field(default=5, description="Rezagos usados en el diagnostico ARCH-LM")
    arch_lm_stat: float = Field(default=0.0, description="Estadistico LM sobre residuos estandarizados")
    arch_lm_p_value: float = Field(default=1.0, description="P-value del diagnostico ARCH-LM")
    arch_lm_conclusion: str = Field(
        default="No calculado",
        description="Lectura del diagnostico ARCH-LM de heterocedasticidad remanente",
    )

    conditional_volatility: list[float] = Field(
        default_factory=list,
        description="Serie de volatilidad condicional del mejor modelo",
    )

    conditional_volatility_by_model: dict[str, list[float]] = Field(
        default_factory=dict,
        description="Serie de volatilidad condicional por modelo candidato",
    )

    ewma_lambda: float = Field(default=0.94, description="Factor lambda usado en EWMA")
    ewma_volatility: list[float] = Field(
        default_factory=list,
        description="Serie de volatilidad EWMA en la misma escala de retornos del modelo",
    )
    ewma_latest_volatility: float | None = Field(
        default=None,
        description="Ultima volatilidad estimada por EWMA",
    )
    ewma_forecast: list[GarchForecastPoint] = Field(
        default_factory=list,
        description="Pronostico EWMA; se mantiene constante si no hay nuevo choque observado",
    )

    rolling_volatility_window: int = Field(
        default=20,
        description="Ventana usada para volatilidad muestral rodante",
    )
    rolling_volatility: list[float] = Field(
        default_factory=list,
        description="Volatilidad muestral rodante usada como comparación contra EWMA",
    )

    forecast: list[GarchForecastPoint] = Field(
        default_factory=list,
        description="Pronostico del mejor modelo",
    )

    forecast_by_model: dict[str, list[float]] = Field(
        default_factory=dict,
        description="Pronostico por modelo candidato",
    )

    effective_forecast_horizon: int
    mode: str
    summary: str
