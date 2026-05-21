from __future__ import annotations

from typing import Any

from ui.asset_metadata import display_country


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


def _country_code(asset: dict[str, Any]) -> str:
    raw = (
        asset.get("country")
        or asset.get("pais")
        or asset.get("country_code")
        or display_country(asset)
        or ""
    )
    country = str(raw).strip().upper()
    if country.startswith("ESTADOS UNIDOS"):
        return "US"
    if country in US_ALIASES:
        return "US"
    return country or "N/D"


def _looks_global(asset: dict[str, Any]) -> bool:
    text = " ".join(
        str(asset.get(key, ""))
        for key in ("name", "ticker", "country", "category", "asset_type", "benchmark_ticker")
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
    has_global_exposure = any(_looks_global(asset) for asset in assets)

    if countries <= {"US"} and not has_global_exposure:
        return {
            "ticker": "SPY",
            "name": "S&P 500 ETF",
            "criterion": "us_only",
            "reason": "Todos los activos son de Estados Unidos.",
            "explanation": "Se usa SPY como proxy descargable del S&P 500 para portafolios 100% estadounidenses.",
        }

    return {
        "ticker": "ACWI",
        "name": "MSCI ACWI ETF",
        "criterion": "global_or_mixed",
        "reason": "Portafolio internacional, mixto, con ADRs, ETFs globales o exposición de distintos países.",
        "explanation": "Se usa ACWI como referencia global para comparar portafolios con exposición internacional.",
    }
