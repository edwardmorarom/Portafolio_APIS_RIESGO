from pydantic import BaseModel, Field, field_validator


class ReturnsStatsRequest(BaseModel):
    ticker: str = Field(..., description="Ticker del activo")
    start: str = Field(default="2021-01-01", description="Fecha inicial")
    end: str = Field(default="2026-12-31", description="Fecha final")
    return_type: str = Field(default="log", description="simple o log")
    mode: str = Field(default="estadistico", description="general o estadistico")

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        value = v.strip().upper()
        if not value:
            raise ValueError("ticker no puede ser vacio")
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


class NormalityTestResult(BaseModel):
    statistic: float | None = Field(default=None)
    p_value: float | None = Field(default=None)
    conclusion: str = Field(...)


class AndersonDarlingResult(BaseModel):
    statistic: float | None = Field(default=None)
    critical_values: list[float] = Field(default_factory=list)
    significance_levels: list[float] = Field(default_factory=list)
    conclusion: str = Field(...)


class HistogramBin(BaseModel):
    left: float
    right: float
    count: int


class QQPoint(BaseModel):
    theoretical: float
    sample: float


class BoxplotSummary(BaseModel):
    min: float
    q1: float
    median: float
    q3: float
    max: float
    outliers: list[float] = Field(default_factory=list)


class ReturnsStatsResponse(BaseModel):
    ticker: str
    start: str
    end: str
    return_type: str
    observations: int
    mean: float
    std: float
    skewness: float
    kurtosis: float
    min_return: float
    max_return: float
    shapiro_wilk: NormalityTestResult
    jarque_bera: NormalityTestResult
    anderson_darling: AndersonDarlingResult
    histogram: list[HistogramBin] = Field(default_factory=list)
    qq_plot: list[QQPoint] = Field(default_factory=list)
    boxplot: BoxplotSummary
    mode: str
    summary: str