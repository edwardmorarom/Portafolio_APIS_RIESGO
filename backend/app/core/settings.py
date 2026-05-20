from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Portafolio Riesgo API", description="Nombre de la aplicaciÃ³n")
    app_version: str = Field(default="0.1.0", description="VersiÃ³n actual de la API")
    app_env: str = Field(default="dev", description="Entorno de ejecuciÃ³n")
    debug: bool = Field(default=True, description="Activa modo debug")

    api_v1_prefix: str = Field(default="/api/v1", description="Prefijo de la API v1")
    database_url: str = Field(
        default="sqlite:///./data/portafolio_riesgo.db",
        description="URL de conexiÃ³n a la base de datos SQLAlchemy",
    )

    default_start_date: str = Field(default="2021-01-01", description="Fecha inicial por defecto")
    default_end_date: str = Field(default="2026-12-31", description="Fecha final por defecto")
    global_benchmark: str = Field(default="ACWI", description="Benchmark global por defecto")
    default_base_currency: str = Field(default="USD", description="Moneda base por defecto")
    rf_ticker_usd: str = Field(default="^IRX    ", description="Ticker de tasa libre de riesgo para USD")
    rf_ticker_eur: str = Field(default="^GDBR10", description="Ticker de tasa libre de riesgo para EUR")
    rf_ticker_cop_proxy: str = Field(default="^TNX", description="Ticker proxy de tasa libre de riesgo para COP")

    fred_api_key: str | None = Field(default=None, description="API key de FRED")

    # Configuraci?n opcional para chatbot con IA real.
    # No se deben quemar claves en c?digo. Usar .env local o secrets del proveedor.
    llm_provider: str = Field(default="local", description="Proveedor LLM para chatbot: local, openai, azure, gemini u otro")
    llm_model: str = Field(default="local-expert", description="Modelo LLM configurado para el chatbot")
    llm_api_key: str | None = Field(default=None, description="API key del proveedor LLM")
    llm_base_url: str | None = Field(default=None, description="URL base opcional del proveedor LLM")

    external_api_timeout_seconds: int = Field(default=20, description="Timeout para APIs externas")
    frontend_base_url: str = Field(default="http://localhost:8501", description="URL del frontend")
    yahoo_timeout_seconds: int = Field(default=20, ge=1, le=120, description="Timeout para datos de mercado")
    macro_timeout_seconds: int = Field(default=20, ge=1, le=120, description="Timeout para datos macro")

    internal_api_key: str | None = Field(default=None, description="API key interna simple para endpoints sensibles")
    allowed_origins: str = Field(
        default="http://localhost:8501,http://127.0.0.1:8501",
        description="OrÃ­genes permitidos separados por coma",
    )
    min_obs_var: int = Field(default=60, ge=30, le=5000, description="Observaciones mÃ­nimas para VaR")
    min_obs_capm: int = Field(default=60, ge=30, le=5000, description="Observaciones mÃ­nimas para CAPM")
    min_obs_portfolio: int = Field(default=60, ge=30, le=5000, description="Observaciones mÃ­nimas para optimización")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
