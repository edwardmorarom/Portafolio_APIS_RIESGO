from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator


class EfficientFrontierRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=2, max_length=15, description="Tickers del portafolio")
    start: str = Field(default="2021-01-01", description="Fecha inicial")
    end: str = Field(default="2026-12-31", description="Fecha final")
    rf_annual: float = Field(default=0.04, ge=0.0, le=1.0, description="Tasa libre de riesgo anual")
    n_portfolios: int = Field(default=5000, ge=1000, le=50000, description="Número de portafolios simulados")
    return_type: str = Field(default="log", description="Tipo de rendimiento: simple o log")
    target_return_annual: float | None = Field(
        default=None,
        ge=-1.0,
        le=5.0,
        description="Rendimiento objetivo anual opcional",
    )
    risk_profile: str | None = Field(
        default=None,
        description="Perfil opcional: conservador, arriesgado, minimo_riesgo, maxima_utilidad",
    )

    @model_validator(mode="before")
    @classmethod
    def map_frontend_aliases(cls, values: dict):
        if not isinstance(values, dict):
            return values

        if "risk_free_rate" in values and "rf_annual" not in values:
            values["rf_annual"] = values["risk_free_rate"]

        if "target_return" in values and "target_return_annual" not in values:
            values["target_return_annual"] = values["target_return"]

        return values

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: list[str]) -> list[str]:
        cleaned = [item.strip().upper() for item in v if item.strip()]
        if len(cleaned) < 2:
            raise ValueError("Debe enviar al menos dos tickers válidos")
        if len(cleaned) > 15:
            raise ValueError("Se permite un máximo de 15 acciones")
        return cleaned

    @field_validator("return_type")
    @classmethod
    def validate_return_type(cls, v: str) -> str:
        value = v.strip().lower()
        if value not in {"simple", "log"}:
            raise ValueError("return_type debe ser 'simple' o 'log'")
        return value

    @field_validator("risk_profile")
    @classmethod
    def validate_risk_profile(cls, v: str | None) -> str | None:
        if v is None:
            return v
        value = v.strip().lower()
        allowed = {"conservador", "arriesgado", "minimo_riesgo", "maxima_utilidad"}
        if value not in allowed:
            raise ValueError("risk_profile no válido")
        return value


class FrontierPoint(BaseModel):
    volatility: float = Field(..., description="Volatilidad anualizada")
    return_: float = Field(..., alias="return", description="Retorno anualizado")
    sharpe: float | None = Field(default=None, description="Sharpe opcional")


class PortfolioWeightsItem(BaseModel):
    asset: str = Field(..., description="Ticker del activo")
    weight: float = Field(..., description="Peso del activo")


class OptimalPortfolio(BaseModel):
    return_: float = Field(..., alias="return", description="Retorno anualizado")
    volatility: float = Field(..., description="Volatilidad anualizada")
    sharpe: float = Field(..., description="Ratio de Sharpe")
    weights: list[PortfolioWeightsItem] = Field(default_factory=list, description="Composición del portafolio")


class TargetReturnPortfolio(BaseModel):
    target_return_annual: float = Field(..., description="Rendimiento objetivo anual")
    achieved_return_annual: float = Field(..., description="Rendimiento anual alcanzado")
    volatility_annual: float = Field(..., description="Volatilidad anual del portafolio objetivo")
    weights: list[PortfolioWeightsItem] = Field(default_factory=list, description="Pesos del portafolio objetivo")


class ProfileSuggestedPortfolio(BaseModel):
    profile: str = Field(..., description="Perfil seleccionado")
    return_: float = Field(..., alias="return", description="Retorno anualizado sugerido")
    volatility: float = Field(..., description="Volatilidad anualizada sugerida")
    sharpe: float = Field(..., description="Sharpe del portafolio sugerido")
    weights: list[PortfolioWeightsItem] = Field(default_factory=list, description="Pesos sugeridos")

class TopPortfolio(BaseModel):
    rank: int = Field(..., description="Posición dentro del ranking")
    return_: float = Field(..., alias="return", description="Retorno anualizado")
    volatility: float = Field(..., description="Volatilidad anualizada")
    sharpe: float = Field(..., description="Ratio de Sharpe")
    weights: list[PortfolioWeightsItem] = Field(default_factory=list, description="Pesos del portafolio")


class PerriObjectiveComparison(BaseModel):
    objective: str = Field(..., description="Objetivo Perri comparado")
    perri_return: float | None = Field(default=None, description="Retorno anual Perri")
    perri_volatility: float | None = Field(default=None, description="Volatilidad anual Perri")
    perri_sharpe: float | None = Field(default=None, description="Sharpe Perri")
    user_return: float = Field(..., description="Retorno anual del portafolio Markowitz del usuario")
    user_volatility: float = Field(..., description="Volatilidad anual del portafolio Markowitz del usuario")
    user_sharpe: float = Field(..., description="Sharpe del portafolio Markowitz del usuario")
    return_gap: float | None = Field(default=None, description="Diferencia de retorno usuario menos Perri")
    volatility_gap: float | None = Field(default=None, description="Diferencia de volatilidad usuario menos Perri")
    sharpe_gap: float | None = Field(default=None, description="Diferencia de Sharpe usuario menos Perri")
    verdict: str = Field(..., description="Resultado interpretativo de la comparación")


class PerriComparison(BaseModel):
    enabled: bool = Field(..., description="Indica si la comparación contra Perri fue posible")
    portfolio_size: int = Field(..., description="Cantidad de activos del portafolio del usuario")
    horizon: str = Field(..., description="Horizonte Perri usado para comparar")
    message: str = Field(..., description="Mensaje general de comparación")
    comparisons: list[PerriObjectiveComparison] = Field(
        default_factory=list,
        description="Comparaciones contra objetivos Perri",
    )


class EfficientFrontierResponse(BaseModel):
    tickers: list[str] = Field(..., description="Tickers analizados")
    start: str = Field(..., description="Fecha inicial")
    end: str = Field(..., description="Fecha final")
    rf_annual: float = Field(..., description="Tasa libre de riesgo anual")

    frontier: list[FrontierPoint] = Field(default_factory=list, description="Puntos de la frontera eficiente")
    simulated_portfolios: list[FrontierPoint] = Field(default_factory=list, description="Nube simulada de portafolios")
    correlation_matrix: dict[str, dict[str, float]] = Field(default_factory=dict, description="Matriz de correlación")
    observations: int = Field(..., description="Número de observaciones alineadas")
    n_assets: int = Field(..., description="Número de activos efectivos")

    min_variance: OptimalPortfolio = Field(..., description="Portafolio de mínima varianza")
    max_sharpe: OptimalPortfolio = Field(..., description="Portafolio de máximo Sharpe")
    top_portfolios: list[TopPortfolio] = Field(
        default_factory=list,
        description="Ranking de los 5 mejores portafolios por Sharpe",
    )
    target_return_portfolio: TargetReturnPortfolio | None = Field(
        default=None,
        description="Portafolio asociado a rendimiento objetivo",
    )
    suggested_profile_portfolio: ProfileSuggestedPortfolio | None = Field(
        default=None,
        description="Portafolio sugerido según perfil",
    )
    perri_comparison: PerriComparison | None = Field(
        default=None,
        description="Comparación del portafolio Markowitz contra umbrales institucionales Perri",
    )