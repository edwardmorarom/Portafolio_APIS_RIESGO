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


class ReturnTypeMixin(BaseModel):
    return_type: str = Field(default="log", description="Tipo de rendimiento: simple o log")

    @field_validator("return_type")
    @classmethod
    def validate_return_type(cls, v: str) -> str:
        allowed = {"simple", "log"}
        value = v.strip().lower()
        if value not in allowed:
            raise ValueError("return_type debe ser 'simple' o 'log'")
        return value


class AssetUniverseItem(BaseModel):
    name: str = Field(..., description="Nombre del activo")
    ticker: str = Field(..., description="Ticker del activo")
    country: str = Field(..., description="Pa?s o mercado de referencia")
    default: bool = Field(default=False, description="Indica si pertenece al portafolio base del proyecto")

    asset_type: str | None = Field(
        default=None,
        description="Clase de activo: renta_variable, renta_fija, commodity, etf_sectorial, etf_global o efectivo_o_corto_plazo",
    )
    benchmark_ticker: str | None = Field(
        default=None,
        description="Benchmark recomendado para comparar el activo seg?n su clase",
    )
    benchmark_description: str | None = Field(
        default=None,
        description="Descripci?n metodol?gica del benchmark recomendado",
    )
    include_in_perri: bool = Field(
        default=False,
        description="Indica si el activo est? habilitado para el universo de Perri",
    )
    source: str | None = Field(
        default=None,
        description="Fuente de origen del activo",
    )


class AssetUniverseResponse(BaseModel):
    max_assets_allowed: int = Field(..., description="Máximo de activos permitidos")
    benchmark_ticker: str = Field(..., description="Benchmark global por defecto")
    base_currencies: list[str] = Field(..., description="Monedas base soportadas")
    assets: list[AssetUniverseItem] = Field(default_factory=list, description="Universo de activos")


class AssetSearchResponse(BaseModel):
    query: str = Field(..., description="Texto buscado por el usuario")
    total_matches: int = Field(..., description="Cantidad de coincidencias")
    assets: list[AssetUniverseItem] = Field(default_factory=list, description="Resultados de búsqueda")