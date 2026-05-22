from pydantic import BaseModel, Field


class MacroSnapshotResponse(BaseModel):
    base_currency: str = Field(..., description="Moneda base seleccionada")
    benchmark_ticker: str = Field(..., description="Benchmark global")
    rf_ticker: str = Field(..., description="Ticker usado para la tasa libre de riesgo")

    risk_free_rate_pct: float | None = Field(default=None, description="Tasa libre de riesgo en porcentaje")
    rf_rate_pct: float | None = Field(default=None, description="Alias frontend de tasa libre de riesgo")

    inflation_yoy: float | None = Field(default=None, description="Inflación anual")
    inflation_pct: float | None = Field(default=None, description="Alias frontend de inflación anual")

    cop_per_usd: float | None = Field(default=None, description="Tasa COP por USD")
    usdcop_market: float | None = Field(default=None, description="USD/COP de mercado")
    fx_spot: float | None = Field(default=None, description="Alias frontend del spot FX")

    source: str = Field(..., description="Fuente del dato")
    note: str = Field(..., description="Nota metodológica")
    last_updated: str | None = Field(default=None, description="Última actualización")
    cache_status: str | None = Field(default=None, description="Estado del cache SQLite de 24h")
    indicators: dict = Field(default_factory=dict, description="Indicadores macro con ultimo valor e historia")


class FxSpotResponse(BaseModel):
    base_currency: str = Field(..., description="Moneda base seleccionada")
    quote_currency: str = Field(..., description="Moneda cotizada")
    fx_ticker: str = Field(..., description="Ticker usado para obtener la tasa de cambio")
    spot: float = Field(..., description="Spot más reciente disponible")
    spot_date: str = Field(..., description="Fecha del último dato disponible")
    rf_ticker: str = Field(..., description="Ticker de tasa libre de riesgo")
    rf_rate_pct: float | None = Field(default=None, description="Tasa libre de riesgo en porcentaje")
    benchmark_ticker: str = Field(..., description="Benchmark por defecto")
    message: str = Field(..., description="Resumen interpretativo")
