from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


CouponFrequency = Literal[1, 2, 4]
AnnualRateType = Literal["nominal_anual", "efectiva_anual"]


class BondPurchaseRequest(BaseModel):
    issue_date: date = Field(..., description="Fecha de emision del bono")
    maturity_date: date = Field(..., description="Fecha de vencimiento del bono")
    settlement_date: date = Field(..., description="Fecha de negociacion o compra")
    face_value: float = Field(..., gt=0, description="Valor nominal monetario")
    coupon_rate: float = Field(..., ge=0, description="Tasa cupon anual en decimal")
    coupon_rate_type: AnnualRateType = Field(default="nominal_anual")
    coupon_frequency: CouponFrequency = Field(default=1, description="Frecuencia: 1 anual, 2 semestral, 4 trimestral")
    market_yield: float = Field(..., ge=0, description="Yield anual de mercado en decimal")
    market_yield_type: AnnualRateType = Field(default="nominal_anual")
    clean_price_pct: float = Field(..., gt=0, description="Precio limpio como porcentaje del valor nominal")
    fees_pct: float = Field(default=0.0, ge=0, description="Honorarios porcentuales sobre precio sucio")
    fixed_fee: float = Field(default=0.0, ge=0, description="Honorario fijo monetario")
    currency: str = Field(default="COP", min_length=3, max_length=3, description="Moneda de visualizacion")

    @model_validator(mode="after")
    def validate_dates(self) -> "BondPurchaseRequest":
        if self.maturity_date <= self.issue_date:
            raise ValueError("fecha vencimiento debe ser mayor que fecha emision")
        if self.settlement_date < self.issue_date:
            raise ValueError("fecha negociacion debe ser mayor o igual que fecha emision")
        if self.settlement_date >= self.maturity_date:
            raise ValueError("fecha negociacion debe ser anterior al vencimiento")
        return self


class BondPurchaseInputs(BaseModel):
    issue_date: date
    maturity_date: date
    settlement_date: date
    face_value: float
    coupon_rate: float
    coupon_rate_type: AnnualRateType
    coupon_frequency: int
    market_yield: float
    market_yield_type: AnnualRateType
    clean_price_pct: float
    fees_pct: float
    fixed_fee: float
    currency: str


class BondPurchaseRates(BaseModel):
    coupon_periodic_rate: float
    market_yield_periodic: float


class BondPurchaseCouponDates(BaseModel):
    previous_coupon_date: date
    next_coupon_date: date
    accrued_days: int
    coupon_period_days: int


class BondPurchaseMetrics(BaseModel):
    coupon_per_period: float
    accrued_interest: float
    clean_price_value: float
    dirty_price: float
    fees: float
    total_purchase: float
    theoretical_price: float
    future_value: float
    expected_gain_simple: float
    buyer_npv: float
    macaulay_duration: float
    modified_duration: float
    dv01: float
    dv01_approx: float
    remaining_periods: int


class BondPurchaseCashflow(BaseModel):
    payment_date: date
    days_from_settlement: int
    period: int
    cashflow: float
    discount_factor: float
    present_value: float


class BondPurchaseResponse(BaseModel):
    position: Literal["purchase"]
    inputs: BondPurchaseInputs
    rates: BondPurchaseRates
    coupon_dates: BondPurchaseCouponDates
    metrics: BondPurchaseMetrics
    cashflows: list[BondPurchaseCashflow]
    interpretation: str
