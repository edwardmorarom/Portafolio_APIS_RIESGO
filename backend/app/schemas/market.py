from pydantic import BaseModel, Field


class PricePoint(BaseModel):
    date: str = Field(..., description="Fecha del dato")
    open: float | None = Field(default=None, description="Precio de apertura")
    high: float | None = Field(default=None, description="Precio máximo")
    low: float | None = Field(default=None, description="Precio mínimo")
    close: float | None = Field(default=None, description="Precio de cierre")
    adj_close: float | None = Field(default=None, description="Precio ajustado")
    volume: float | None = Field(default=None, description="Volumen")


class PricesResponse(BaseModel):
    ticker: str = Field(..., min_length=1, description="Ticker consultado")
    start: str = Field(..., description="Fecha inicial usada")
    end: str = Field(..., description="Fecha final usada")
    message: str = Field(..., description="Mensaje de estado")
    data: list[PricePoint] = Field(default_factory=list, description="Serie histórica de precios")


class ReturnPoint(BaseModel):
    date: str = Field(..., description="Fecha del rendimiento")
    simple_return: float | None = Field(default=None, description="Rendimiento simple")
    log_return: float | None = Field(default=None, description="Rendimiento logarítmico")


class ReturnsResponse(BaseModel):
    ticker: str = Field(..., min_length=1, description="Ticker consultado")
    start: str = Field(..., description="Fecha inicial usada")
    end: str = Field(..., description="Fecha final usada")
    message: str = Field(..., description="Mensaje de estado")
    data: list[ReturnPoint] = Field(default_factory=list, description="Serie de rendimientos")