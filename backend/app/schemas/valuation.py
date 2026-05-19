from __future__ import annotations
from pydantic import BaseModel, Field
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

# --- ESQUEMAS PARA BONOS ---

class BondMetricsRequest(BaseModel):
    face_value: float = Field(..., gt=0)
    coupon_rate: float = Field(..., ge=0)
    maturity_years: int = Field(..., gt=0)
    market_yield: float = Field(..., ge=0)


class BondMetricsResponse(BaseModel):
    price: float
    duration: float
    modified_duration: float
    convexity: float
