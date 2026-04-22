from pydantic import BaseModel, Field
from pydantic import BaseModel, Field, field_validator

class AssetItem(BaseModel):
    name: str = Field(..., description="Nombre de la empresa o activo")
    ticker: str = Field(..., description="Ticker del activo")
    country: str = Field(..., description="País principal del activo")


class AssetsResponse(BaseModel):
    assets: list[AssetItem] = Field(default_factory=list, description="Lista de activos disponibles")


class MacroQueryParams(BaseModel):
    base_currency: str = Field(default="USD", description="Moneda base del análisis")

    @field_validator("base_currency")
    @classmethod
    def validate_base_currency(cls, v: str) -> str:
        allowed = {"USD", "EUR", "COP"}
        value = v.strip().upper()
        if value not in allowed:
            raise ValueError("base_currency debe ser USD, EUR o COP")
        return value