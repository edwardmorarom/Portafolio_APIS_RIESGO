from __future__ import annotations

from typing import Any

from ui.asset_metadata import ETF_COUNTRIES, US_TICKERS, display_country


US_ALIASES = {
    "US",
    "USA",
    "UNITED STATES",
    "ESTADOS UNIDOS",
    "ESTADOS UNIDOS DE AMERICA",
}

GLOBAL_MARKERS = {
    "GLOBAL",
    "WORLD",
    "INTERNATIONAL",
    "INTERNACIONAL",
    "EMERGING",
    "EMERGENTES",
    "DEVELOPED",
    "DESARROLLADOS",
    "MSCI ACWI",
}

US_EQUITY_ETFS = {
    ticker
    for ticker, country in ETF_COUNTRIES.items()
    if str(country).upper().startswith("ESTADOS UNIDOS") and "RENTA FIJA" not in str(country).upper()
}

FIXED_INCOME_TICKERS = {
    ticker
    for ticker, country in ETF_COUNTRIES.items()
    if any(token in str(country).upper() for token in ["RENTA FIJA", "BONOS", "TESORO", "CRÉDITO", "CREDITO", "HIGH YIELD"])
}


def _country_code(asset: dict[str, Any]) -> str:
    raw = (
        asset.get("country")
        or asset.get("pais")
        or asset.get("country_code")
        or display_country(asset)
        or ""
    )
    country = str(raw).strip().upper()
    if country in {"GLOBAL / US-LISTED", "N/D"}:
        country = str(display_country(asset)).strip().upper()
    if country.startswith("ESTADOS UNIDOS"):
        return "US"
    if country in US_ALIASES:
        return "US"
    return country or "N/D"


def _asset_type_key(asset: dict[str, Any]) -> str:
    raw_type = (
        asset.get("asset_type")
        or asset.get("tipo_activo")
        or asset.get("type")
        or asset.get("category")
        or ""
    )
    normalized = str(raw_type).strip().lower()
    ticker = str(asset.get("ticker", "")).strip().upper()
    name = str(asset.get("name", "")).lower()

    if normalized in {"renta_fija", "fixed_income", "bond", "bonds"}:
        return "renta_fija"
    if normalized in {"renta_variable", "equity", "stock", "stocks", "accion", "acciones", "etf_sectorial"}:
        return "renta_variable"
    if normalized in {"etf_global", "commodity", "efectivo_o_corto_plazo"}:
        return normalized
    if ticker in FIXED_INCOME_TICKERS or any(token in name for token in ["bond", "treasury", "bono", "deuda"]):
        return "renta_fija"
    if ticker in US_TICKERS or ticker in US_EQUITY_ETFS:
        return "renta_variable"

    return normalized or "renta_variable"


def _looks_global(asset: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(asset.get("name", "")),
            str(asset.get("ticker", "")),
            display_country(asset),
            str(asset.get("category", "")),
            str(asset.get("asset_type", "")),
        ]
    ).upper()
    return any(marker in text for marker in GLOBAL_MARKERS)


def resolve_benchmark(selected_assets: list[dict[str, Any]] | None) -> dict[str, str]:
    assets = [asset for asset in (selected_assets or []) if isinstance(asset, dict)]

    if not assets:
        return {
            "ticker": "ACWI",
            "name": "MSCI ACWI",
            "criterion": "default",
            "reason": "Benchmark global por defecto hasta seleccionar activos.",
            "explanation": "Sin activos seleccionados se usa ACWI como referencia global descargable.",
        }

    countries = {_country_code(asset) for asset in assets}
    asset_types = {_asset_type_key(asset) for asset in assets}
    has_global_exposure = any(_looks_global(asset) for asset in assets)

    if countries <= {"US"} and asset_types <= {"renta_variable"} and not has_global_exposure:
        return {
            "ticker": "SPY",
            "name": "S&P 500 ETF",
            "criterion": "us_equity_only",
            "reason": "Todos los activos son de Estados Unidos y de renta variable.",
            "explanation": "Se usa SPY como proxy descargable del S&P 500 para portafolios 100% estadounidenses de renta variable.",
        }

    return {
        "ticker": "ACWI",
        "name": "MSCI ACWI ETF",
        "criterion": "global_or_mixed",
        "reason": "Portafolio internacional, mixto, con ADRs, ETFs globales o exposición de distintos países.",
        "explanation": "Se usa ACWI como referencia global para comparar portafolios con exposición internacional.",
    }
