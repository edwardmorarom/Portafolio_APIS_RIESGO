from pydantic import BaseModel, Field, field_validator, model_validator


class AlertsResponseItem(BaseModel):
    indicator: str = Field(..., description="Nombre del indicador")
    rule: str = Field(..., description="Regla tecnica evaluada")
    status: str = Field(..., description="Estado: normal, watch o alert")
    signal: str = Field(..., description="Tipo de señal")
    severity: str = Field(..., description="Nivel de severidad")
    value: float | None = Field(default=None, description="Valor actual del indicador")
    threshold_low: float | None = Field(default=None, description="Umbral inferior")
    threshold_high: float | None = Field(default=None, description="Umbral superior")
    general_message: str = Field(..., description="Interpretación simple")
    statistical_message: str = Field(..., description="Interpretación técnica")


class AlertsResponse(BaseModel):
    ticker: str = Field(..., description="Ticker analizado")
    start: str = Field(..., description="Fecha inicial")
    end: str = Field(..., description="Fecha final")
    alerts: list[AlertsResponseItem] = Field(default_factory=list, description="Estado y alertas detectadas")
    total_alerts: int = Field(..., description="Cantidad total de alertas activas")


class AlertsRequestParams(BaseModel):
    ticker: str = Field(..., description="Ticker del activo")
    start: str = Field(default="2021-01-01", description="Fecha inicial")
    end: str = Field(default="2026-12-31", description="Fecha final")
    rsi_overbought: float = Field(default=70.0, ge=50.0, le=100.0)
    rsi_oversold: float = Field(default=30.0, ge=0.0, le=50.0)
    stoch_overbought: float = Field(default=80.0, ge=50.0, le=100.0)
    stoch_oversold: float = Field(default=20.0, ge=0.0, le=50.0)
    sma_short_window: int = Field(default=20, ge=2, le=120)
    sma_long_window: int = Field(default=50, ge=5, le=260)

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        value = v.strip().upper()
        if not value:
            raise ValueError("ticker no puede ser vacio")
        return value

    @model_validator(mode="after")
    def validate_moving_average_windows(self):
        if self.sma_short_window >= self.sma_long_window:
            raise ValueError("sma_short_window debe ser menor que sma_long_window")
        return self
