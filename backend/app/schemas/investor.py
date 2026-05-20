from __future__ import annotations

from datetime import date
from pydantic import BaseModel, Field, field_validator, model_validator


class InvestorPreferencesRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=1, max_length=15, description="Tickers seleccionados")
    weights_pct: list[float] = Field(..., min_length=1, max_length=15, description="Pesos en porcentaje")
    base_currency: str = Field(default="USD", description="Moneda base: USD, EUR o COP")
    confidence_level: float = Field(
        default=0.95,
        ge=0.10,
        le=0.99,
        description="Nivel de confianza entre 0.10 y 0.99",
    )
    risk_profile: str = Field(
        default="conservador",
        description="Perfil: conservador, moderado o agresivo",
    )
    horizon_type: str = Field(
        default="1y",
        description="Horizonte: 1y, 2y, 3y, 5y o custom",
    )
    start: str | None = Field(default=None, description="Fecha inicial si horizon_type=custom")
    end: str | None = Field(default=None, description="Fecha final si horizon_type=custom")
    return_type: str = Field(default="log", description="simple o log")
    target_return_annual: float | None = Field(
        default=None,
        ge=-1.0,
        le=5.0,
        description="Rendimiento objetivo anual opcional",
    )
    mode: str = Field(default="general", description="general o estadistico")

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: list[str]) -> list[str]:
        cleaned = [item.strip().upper() for item in v if item.strip()]
        if not cleaned:
            raise ValueError("Debe enviar al menos un ticker válido")
        if len(cleaned) > 15:
            raise ValueError("Se permite un máximo de 15 acciones")
        return cleaned

    @field_validator("weights_pct")
    @classmethod
    def validate_weights_pct_range(cls, v: list[float]) -> list[float]:
        for w in v:
            if w < 0 or w > 100:
                raise ValueError("Cada peso debe estar entre 0 y 100")
        total = sum(v)
        if abs(total - 100.0) > 1e-6:
            raise ValueError("Los pesos deben sumar 100%")
        return v

    @field_validator("base_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        value = v.strip().upper()
        if value not in {"USD", "EUR", "COP"}:
            raise ValueError("base_currency debe ser USD, EUR o COP")
        return value

    @field_validator("risk_profile")
    @classmethod
    def validate_risk_profile(cls, v: str) -> str:
        value = v.strip().lower()
        allowed = {"conservador", "moderado", "agresivo"}
        if value not in allowed:
            raise ValueError("risk_profile no válido")
        return value

    @field_validator("horizon_type")
    @classmethod
    def validate_horizon_type(cls, v: str) -> str:
        value = v.strip().lower()
        if value not in {"1y", "2y", "3y", "5y", "custom"}:
            raise ValueError("horizon_type debe ser 1y, 2y, 3y, 5y o custom")
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

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "InvestorPreferencesRequest":
        if len(self.tickers) != len(self.weights_pct):
            raise ValueError("La cantidad de tickers y pesos debe coincidir")

        if self.horizon_type == "custom":
            if not self.start or not self.end:
                raise ValueError("Si horizon_type es custom, debe enviar start y end")
            start_date = date.fromisoformat(self.start)
            end_date = date.fromisoformat(self.end)
            today = date.today()
            if start_date >= end_date:
                raise ValueError("La fecha inicial debe ser menor que la final")
            if end_date > today:
                raise ValueError("No se permiten fechas futuras")
        else:
            if self.start is not None or self.end is not None:
                pass

        return self


class InvestorPreferencesResponse(BaseModel):
    tickers: list[str]
    weights_pct: list[float]
    weights_decimal: list[float]
    base_currency: str
    confidence_level: float
    risk_profile: str
    horizon_type: str
    start: str
    end: str
    return_type: str
    mode: str
    target_return_annual: float | None = None
    message: str
class KYCProfileRequest(BaseModel):
    age: int = Field(..., ge=18, le=100, description="Edad del inversionista")
    experience: int = Field(..., ge=0, le=60, description="Anios de experiencia invirtiendo")
    tolerance: int = Field(..., ge=1, le=5, description="Tolerancia al riesgo de 1 a 5")


class KYCProfileResponse(BaseModel):
    suggested_profile: str
    score: int
    explanation: str
