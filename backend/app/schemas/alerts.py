from pydantic import BaseModel, Field, field_validator


class AlertsResponseItem(BaseModel):
    indicator: str = Field(..., description="Nombre del indicador")
    signal: str = Field(..., description="Tipo de señal")
    severity: str = Field(..., description="Nivel de severidad")
    general_message: str = Field(..., description="Interpretación simple")
    statistical_message: str = Field(..., description="Interpretación técnica")


class AlertsResponse(BaseModel):
    ticker: str = Field(..., description="Ticker analizado")
    start: str = Field(..., description="Fecha inicial")
    end: str = Field(..., description="Fecha final")
    alerts: list[AlertsResponseItem] = Field(default_factory=list, description="Alertas detectadas")
    total_alerts: int = Field(..., description="Cantidad total de alertas")


class AlertsRequestParams(BaseModel):
    ticker: str = Field(..., description="Ticker del activo")
    start: str = Field(default="2021-01-01", description="Fecha inicial")
    end: str = Field(default="2026-12-31", description="Fecha final")

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        value = v.strip().upper()
        if not value:
            raise ValueError("ticker no puede ser vacio")
        return value