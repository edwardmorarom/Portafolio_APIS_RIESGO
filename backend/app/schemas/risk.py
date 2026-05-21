from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PortfolioVarRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=1, description="Lista de tickers del portafolio")
    weights: list[float] = Field(..., min_length=1, description="Pesos del portafolio")
    start: str = Field(default="2021-01-01", description="Fecha inicial")
    end: str = Field(default="2026-12-31", description="Fecha final")
    alpha: float = Field(
        default=0.95,
        ge=0.95,
        le=0.9999,
        description="Nivel de confianza entre 95% y 99.99%",
    )
    n_sim: int = Field(default=10000, ge=1000, le=200000, description="Número de simulaciones Monte Carlo")
    return_type: str = Field(default="log", description="Tipo de rendimiento: simple o log")
    distribution: str = Field(
        default="normal",
        description="Distribución usada en VaR paramétrico y Monte Carlo: normal o t-Student",
    )

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

    @field_validator("distribution")
    @classmethod
    def validate_distribution(cls, v: str) -> str:
        value = v.strip().lower()
        if value in {"student", "student-t", "t-student", "t_student"}:
            value = "t"
        if value not in {"normal", "t"}:
            raise ValueError("distribution debe ser 'normal' o 't'")
        return value


class VarMethodResult(BaseModel):
    var_daily: float = Field(..., description="VaR diario")
    cvar_daily: float = Field(..., description="CVaR diario")
    var_annualized: float = Field(..., description="VaR anualizado")
    cvar_annualized: float = Field(..., description="CVaR anualizado")
    distribution: str | None = Field(default=None, description="Distribución usada, si aplica")


class KupiecBacktestResult(BaseModel):
    method: str = Field(..., description="Método de VaR evaluado")
    var_daily: float = Field(..., description="VaR diario usado como umbral de backtesting")
    observations: int = Field(..., description="Número de observaciones usadas en el test")
    violations: int = Field(..., description="Número de excepciones observadas")
    expected_violations: float = Field(..., description="Número esperado de excepciones")
    observed_rate: float = Field(..., description="Frecuencia observada de excepciones")
    expected_rate: float = Field(..., description="Frecuencia esperada de excepciones")
    lr_stat: float = Field(..., description="Estadístico LR del test de Kupiec")
    p_value: float = Field(..., description="P-value del test de Kupiec")
    decision: str = Field(..., description="Decisión estadística del test")
    interpretation: str = Field(..., description="Interpretación breve del backtesting")
    conclusion: str = Field(..., description="Conclusión textual del backtesting")


class PortfolioVarResponse(BaseModel):
    tickers: list[str] = Field(..., description="Tickers del portafolio")
    weights: list[float] = Field(..., description="Pesos del portafolio")
    alpha: float = Field(..., description="Nivel de confianza")
    start: str = Field(..., description="Fecha inicial")
    end: str = Field(..., description="Fecha final")
    distribution: str = Field(default="normal", description="Distribución seleccionada")
    distribution_label: str = Field(default="Normal", description="Etiqueta legible de distribución")

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
        description="Backtesting VaR histórico con test de Kupiec. Campo mantenido por compatibilidad.",
    )
    kupiec_tests: dict[str, KupiecBacktestResult] = Field(
        default_factory=dict,
        description="Backtesting de Kupiec separado por método: historical, parametric y monte_carlo",
    )
