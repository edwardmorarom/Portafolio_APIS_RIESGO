from pydantic import BaseModel, Field, field_validator


class DecisionPanelRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=2, description="Tickers del portafolio")
    weights: list[float] = Field(..., min_length=2, description="Pesos del portafolio")
    benchmark_ticker: str = Field(default="ACWI", description="Ticker del benchmark")
    base_currency: str = Field(default="USD", description="Moneda base")
    start: str = Field(default="2021-01-01", description="Fecha inicial")
    end: str = Field(default="2026-12-31", description="Fecha final")
    alpha: float = Field(default=0.95, ge=0.80, le=0.999, description="Nivel de confianza VaR")
    n_sim: int = Field(default=10000, ge=1000, le=200000, description="Número de simulaciones VaR")
    n_portfolios: int = Field(default=5000, ge=1000, le=50000, description="Número de portafolios simulados")
    return_type: str = Field(default="log", description="Tipo de rendimiento: simple o log")

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: list[str]) -> list[str]:
        cleaned = [item.strip().upper() for item in v if item.strip()]
        if len(cleaned) < 2:
            raise ValueError("Debe enviar al menos dos tickers válidos")
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


class DecisionPanelResponse(BaseModel):
    tickers: list[str] = Field(..., description="Tickers del portafolio")
    weights: list[float] = Field(..., description="Pesos del portafolio")
    benchmark_ticker: str = Field(..., description="Ticker benchmark")
    base_currency: str = Field(..., description="Moneda base")
    rf_ticker: str = Field(..., description="Ticker de tasa libre de riesgo")
    rf_rate_pct: float | None = Field(default=None, description="Tasa libre de riesgo")
    portfolio_beta: float = Field(..., description="Beta del portafolio")
    portfolio_return_annual: float = Field(..., description="Retorno anualizado del portafolio")
    benchmark_return_annual: float = Field(..., description="Retorno anualizado del benchmark")
    capm_expected_return: float = Field(..., description="Retorno esperado CAPM")
    alpha_simple: float = Field(..., description="Alpha simple")
    historical_var_daily: float = Field(..., description="VaR histórico diario")
    historical_cvar_daily: float = Field(..., description="CVaR histórico diario")
    monte_carlo_var_daily: float = Field(..., description="VaR Monte Carlo diario")
    monte_carlo_cvar_daily: float = Field(..., description="CVaR Monte Carlo diario")
    min_variance_return: float = Field(..., description="Retorno del portafolio de mínima varianza")
    max_sharpe_return: float = Field(..., description="Retorno del portafolio de máximo Sharpe")
    stance: str = Field(..., description="Postura sugerida")
    summary: str = Field(..., description="Resumen interpretativo")
    start: str = Field(..., description="Fecha inicial")
    end: str = Field(..., description="Fecha final")