from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PortfolioVarRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=1, description="Lista de tickers del portafolio")
    weights: list[float] = Field(..., min_length=1, description="Pesos del portafolio")
    start: str = Field(default="2021-01-01", description="Fecha inicial")
    end: str = Field(default="2026-12-31", description="Fecha final")
    alpha: float = Field(default=0.95,ge=0.95,le=0.9999,description="Nivel de confianza entre 95% y 99.99%",)
    n_sim: int = Field(default=10000, ge=1000, le=200000, description="Número de simulaciones Monte Carlo")
    return_type: str = Field(default="log", description="Tipo de rendimiento: simple o log")

    @field_validator("weights")
    @classmethod
    def validate_weights_sum(cls, v: list[float]) -> list[float]:
        total = sum(v)
        if abs(total - 1.0) > 1e-6:
            raise ValueError("Los pesos deben sumar 1.0")
        return v

    @field_validator("tickers")
    @classmethod
    def validate_tickers_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Debe enviar al menos un ticker")
        return [item.strip().upper() for item in v]

    @field_validator("return_type")
    @classmethod
    def validate_return_type(cls, v: str) -> str:
        value = v.strip().lower()
        if value not in {"simple", "log"}:
            raise ValueError("return_type debe ser 'simple' o 'log'")
        return value


class VarMethodResult(BaseModel):
    var_daily: float = Field(..., description="VaR diario")
    cvar_daily: float = Field(..., description="CVaR diario")
    var_annualized: float = Field(..., description="VaR anualizado")
    cvar_annualized: float = Field(..., description="CVaR anualizado")


class KupiecBacktestResult(BaseModel):
    violations: int = Field(..., description="Número de violaciones observadas")
    observed_rate: float = Field(..., description="Frecuencia observada de violaciones")
    expected_rate: float = Field(..., description="Frecuencia esperada de violaciones")
    p_value: float = Field(..., description="P-value del test de Kupiec")
    conclusion: str = Field(..., description="Conclusión textual del backtesting")


class PortfolioVarResponse(BaseModel):
    tickers: list[str] = Field(..., description="Tickers del portafolio")
    weights: list[float] = Field(..., description="Pesos del portafolio")
    alpha: float = Field(..., description="Nivel de confianza")
    start: str = Field(..., description="Fecha inicial")
    end: str = Field(..., description="Fecha final")

    parametric: VarMethodResult = Field(..., description="VaR y CVaR paramétricos")
    historical: VarMethodResult = Field(..., description="VaR y CVaR históricos")
    monte_carlo: VarMethodResult = Field(..., description="VaR y CVaR por simulación Monte Carlo")

    portfolio_returns: list[float] = Field(
        default_factory=list,
        description="Distribución histórica de rendimientos del portafolio",
    )
    simulated_returns: list[float] = Field(
        default_factory=list,
        description="Distribución simulada de rendimientos Monte Carlo",
    )

    kupiec_test: KupiecBacktestResult | None = Field(
        default=None,
        description="Backtesting VaR con test de Kupiec",
    )