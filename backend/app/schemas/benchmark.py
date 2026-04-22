from pydantic import BaseModel, Field, field_validator


class BenchmarkCompareRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=1, max_length=15, description="Tickers del portafolio")
    weights: list[float] = Field(..., min_length=1, max_length=15, description="Pesos del portafolio en decimales")
    benchmark_ticker: str = Field(default="ACWI", description="Ticker del benchmark")
    base_currency: str = Field(default="USD", description="Moneda base")
    start: str = Field(default="2021-01-01", description="Fecha inicial")
    end: str = Field(default="2026-12-31", description="Fecha final")
    return_type: str = Field(default="log", description="simple o log")
    mode: str = Field(default="estadistico", description="general o estadistico")

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: list[str]) -> list[str]:
        cleaned = [item.strip().upper() for item in v if item.strip()]
        if not cleaned:
            raise ValueError("Debe enviar al menos un ticker")
        if len(cleaned) > 15:
            raise ValueError("Se permite un máximo de 15 acciones")
        return cleaned

    @field_validator("weights")
    @classmethod
    def validate_weights_sum(cls, v: list[float]) -> list[float]:
        if abs(sum(v) - 1.0) > 1e-6:
            raise ValueError("Los pesos deben sumar 1.0")
        return v

    @field_validator("base_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        value = v.strip().upper()
        if value not in {"USD", "EUR", "COP"}:
            raise ValueError("base_currency debe ser USD, EUR o COP")
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


class BenchmarkMetrics(BaseModel):
    cumulative_return: float = Field(..., description="Rendimiento acumulado")
    annual_return: float = Field(..., description="Rendimiento anualizado")
    annual_volatility: float = Field(..., description="Volatilidad anualizada")
    sharpe: float = Field(..., description="Ratio de Sharpe")
    max_drawdown: float = Field(..., description="Máximo drawdown")


class BenchmarkCompareResponse(BaseModel):
    tickers: list[str] = Field(..., description="Tickers del portafolio")
    weights: list[float] = Field(..., description="Pesos del portafolio")
    benchmark_ticker: str = Field(..., description="Ticker benchmark")
    base_currency: str = Field(..., description="Moneda base")
    rf_ticker: str = Field(..., description="Ticker de tasa libre de riesgo")
    rf_rate_pct: float | None = Field(default=None, description="Tasa libre de riesgo")
    portfolio: BenchmarkMetrics = Field(..., description="Métricas del portafolio")
    benchmark: BenchmarkMetrics = Field(..., description="Métricas del benchmark")
    alpha_jensen: float = Field(..., description="Alpha de Jensen")
    tracking_error: float = Field(..., description="Tracking error anualizado")
    information_ratio: float = Field(..., description="Information ratio")
    mode: str = Field(..., description="Modo de salida")
    summary: str = Field(..., description="Resumen interpretativo")
    start: str = Field(..., description="Fecha inicial")
    end: str = Field(..., description="Fecha final")