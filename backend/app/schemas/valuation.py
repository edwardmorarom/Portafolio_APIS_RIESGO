from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict

# --- ESQUEMAS PARA NELSON-SIEGEL ---
class YieldCurveRequest(BaseModel):
    yields: List[float] = Field(..., description="Lista de tasas observadas")
    maturities: List[float] = Field(..., description="Lista de plazos/vencimientos en aÃ±os")

class NelsonSiegelParams(BaseModel):
    tau: float
    beta0: float
    beta1: float
    beta2: float

class YieldCurveResponse(BaseModel):
    params: NelsonSiegelParams
    rmse: float
    curve_type: str
    summary: str

# --- ESQUEMAS PARA BLACK-SCHOLES ---
class OptionValuationRequest(BaseModel):
    spot_price: float = Field(..., gt=0)
    strike_price: float = Field(..., gt=0)
    time_to_maturity: float = Field(..., gt=0, description="Tiempo en aÃ±os")
    risk_free_rate: float = Field(..., description="Tasa anualizada (ej: 0.05)")
    volatility: float = Field(..., gt=0, description="Volatilidad anualizada")
    option_type: str = Field("call", pattern="^(call|put)$")

class Greeks(BaseModel):
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float

class OptionValuationResponse(BaseModel):
    price: float
    greeks: Greeks
    params: Dict[str, float]


class OptionPricingRequest(BaseModel):
    S: float = Field(..., gt=0, description="Precio actual del subyacente")
    K: float = Field(..., gt=0, description="Strike de la opcion")
    T: float = Field(..., description="Tiempo a vencimiento en anos")
    r: float = Field(..., description="Tasa libre de riesgo anual")
    sigma: float = Field(..., description="Volatilidad anualizada")
    tipo: str = Field(..., description="call o put")

    @field_validator("T")
    @classmethod
    def validate_t(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("T debe ser mayor que 0")
        return value

    @field_validator("sigma")
    @classmethod
    def validate_sigma(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("sigma debe ser mayor que 0")
        return value

    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"call", "put"}:
            raise ValueError('tipo debe ser "call" o "put"')
        return normalized


class OptionPricingResponse(BaseModel):
    price: float
    greeks: Greeks
    params: Dict[str, float]

# --- ESQUEMAS PARA BONOS ---

class BondMetricsRequest(BaseModel):
    face_value: float = Field(..., gt=0)
    coupon_rate: float = Field(..., ge=0)
    maturity_years: int = Field(..., gt=0)
    market_yield: float = Field(..., ge=0)


class BondSensitivityPoint(BaseModel):
    shock_bp: int
    shocked_yield: float
    price_linear_duration: float
    price_duration_convexity: float
    price_exact_reprice: float
    pct_change_linear_duration: float
    pct_change_duration_convexity: float
    pct_change_exact_reprice: float


class BondMetricsResponse(BaseModel):
    price: float
    duration: float
    modified_duration: float
    convexity: float
    sensitivity: list[BondSensitivityPoint] = Field(default_factory=list)
