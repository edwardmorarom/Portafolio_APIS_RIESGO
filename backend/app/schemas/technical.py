from pydantic import BaseModel, Field


class TechnicalPoint(BaseModel):
    date: str = Field(..., description="Fecha del dato")
    close: float | None = Field(default=None, description="Precio de cierre")
    sma_20: float | None = Field(default=None, description="Media móvil simple 20")
    ema_20: float | None = Field(default=None, description="Media móvil exponencial 20")
    rsi_14: float | None = Field(default=None, description="RSI de 14 periodos")
    macd: float | None = Field(default=None, description="MACD")
    macd_signal: float | None = Field(default=None, description="Línea de señal MACD")
    macd_hist: float | None = Field(default=None, description="Histograma MACD")
    bb_mid: float | None = Field(default=None, description="Banda media de Bollinger")
    bb_up: float | None = Field(default=None, description="Banda superior de Bollinger")
    bb_low: float | None = Field(default=None, description="Banda inferior de Bollinger")
    stoch_k: float | None = Field(default=None, description="%K del estocástico")
    stoch_d: float | None = Field(default=None, description="%D del estocástico")


class TechnicalResponse(BaseModel):
    ticker: str = Field(..., description="Ticker consultado")
    start: str = Field(..., description="Fecha inicial")
    end: str = Field(..., description="Fecha final")
    message: str = Field(..., description="Mensaje de estado")
    data: list[TechnicalPoint] = Field(default_factory=list, description="Serie con indicadores técnicos")