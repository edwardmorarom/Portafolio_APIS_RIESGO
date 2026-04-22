from pydantic import BaseModel, Field, field_validator


class CapmResponse(BaseModel):
    ticker: str = Field(..., description="Ticker del activo")
    benchmark_ticker: str = Field(..., description="Ticker del benchmark")
    base_currency: str = Field(..., description="Moneda base")
    rf_ticker: str = Field(..., description="Ticker de la tasa libre de riesgo")
    rf_rate_pct: float | None = Field(default=None, description="Tasa libre de riesgo en porcentaje")
    beta: float = Field(..., description="Beta del activo frente al benchmark")
    asset_return_annual: float = Field(..., description="Retorno anualizado del activo")
    benchmark_return_annual: float = Field(..., description="Retorno anualizado del benchmark")
    capm_expected_return: float = Field(..., description="Retorno esperado por CAPM")
    alpha_simple: float = Field(..., description="Alpha simple frente a CAPM")
    start: str = Field(..., description="Fecha inicial")
    end: str = Field(..., description="Fecha final")


class PortfolioCapmRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=1, description="Tickers del portafolio")
    weights: list[float] = Field(..., min_length=1, description="Pesos del portafolio")
    benchmark_ticker: str = Field(default="ACWI", description="Ticker del benchmark")
    base_currency: str = Field(default="USD", description="Moneda base")
    start: str = Field(default="2021-01-01", description="Fecha inicial")
    end: str = Field(default="2026-12-31", description="Fecha final")
    return_type: str = Field(default="log", description="Tipo de rendimiento: simple o log")

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: list[str]) -> list[str]:
        cleaned = [item.strip().upper() for item in v if item.strip()]
        if not cleaned:
            raise ValueError("Debe enviar al menos un ticker")
        return cleaned

    @field_validator("weights")
    @classmethod
    def validate_weights_sum(cls, v: list[float]) -> list[float]:
        total = sum(v)
        if abs(total - 1.0) > 1e-6:
            raise ValueError("Los pesos deben sumar 1.0")
        return v

    @field_validator("base_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        allowed = {"USD", "EUR", "COP"}
        value = v.strip().upper()
        if value not in allowed:
            raise ValueError("base_currency debe ser USD, EUR o COP")
        return value

    @field_validator("return_type")
    @classmethod
    def validate_return_type(cls, v: str) -> str:
        value = v.strip().lower()
        if value not in {"simple", "log"}:
            raise ValueError("return_type debe ser 'simple' o 'log'")
        return value

class PortfolioCapmResponse(BaseModel):
    tickers: list[str] = Field(..., description="Tickers del portafolio")
    weights: list[float] = Field(..., description="Pesos del portafolio")
    benchmark_ticker: str = Field(..., description="Ticker del benchmark")
    base_currency: str = Field(..., description="Moneda base")
    rf_ticker: str = Field(..., description="Ticker de la tasa libre de riesgo")
    rf_rate_pct: float | None = Field(default=None, description="Tasa libre de riesgo en porcentaje")
    portfolio_beta: float = Field(..., description="Beta del portafolio")
    portfolio_return_annual: float = Field(..., description="Retorno anualizado del portafolio")
    benchmark_return_annual: float = Field(..., description="Retorno anualizado del benchmark")
    capm_expected_return: float = Field(..., description="Retorno esperado del portafolio por CAPM")
    alpha_simple: float = Field(..., description="Alpha simple del portafolio")
    start: str = Field(..., description="Fecha inicial")
    end: str = Field(..., description="Fecha final")