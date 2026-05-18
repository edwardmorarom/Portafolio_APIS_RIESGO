from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CACHE_PATH = PROJECT_ROOT / "roboadvisor_cache.csv"
OUTPUT_PATH = PROJECT_ROOT / "backend" / "data" / "perri_universe.json"


FIXED_INCOME_TICKERS = {
    "AGG",
    "BKLN",
    "BND",
    "BNDX",
    "BSV",
    "EMB",
    "FLOT",
    "GOVT",
    "HYG",
    "IEF",
    "IGSB",
    "JNK",
    "LQD",
    "MUB",
    "SHY",
    "SPIP",
    "TIP",
    "TLT",
    "VCIT",
    "VCSH",
}

COMMODITY_TICKERS = {
    "CORN",
    "CPER",
    "DBA",
    "GLD",
    "IAU",
    "PDBC",
    "SLV",
    "UNG",
    "USO",
    "WEAT",
}

SECTOR_ETF_TICKERS = {
    "XLB",
    "XLE",
    "XLF",
    "XLI",
    "XLK",
    "XLP",
    "XLRE",
    "XLU",
    "XLV",
    "XLY",
}

GLOBAL_ETF_TICKERS = {
    "DIA",
    "EEM",
    "EFA",
    "IWM",
    "QQQ",
    "SPY",
    "VEA",
    "VNQ",
    "VTI",
    "VWO",
}

SHORT_TERM_OR_CASH_TICKERS = {
    "FLOT",
    "SHY",
    "BSV",
    "VCSH",
    "IGSB",
}


def classify_asset(ticker: str) -> str:
    if ticker in SHORT_TERM_OR_CASH_TICKERS:
        return "efectivo_o_corto_plazo"

    if ticker in FIXED_INCOME_TICKERS:
        return "renta_fija"

    if ticker in COMMODITY_TICKERS:
        return "commodity"

    if ticker in SECTOR_ETF_TICKERS:
        return "etf_sectorial"

    if ticker in GLOBAL_ETF_TICKERS:
        return "etf_global"

    return "renta_variable"


def expected_currency(ticker: str) -> str:
    """
    Clasificación inicial de moneda para el universo Perri actual.

    El cache actual usa tickers tipo US-listed, ETFs y ADRs sin sufijo regional.
    Por eso se asume USD en esta primera versión.

    Cuando se incluyan tickers con sufijos como .L, .PA, .TO, .MX o .T,
    esta función debe ampliarse para asignar GBP, EUR, CAD, MXN o JPY.
    """
    suffix_currency_map = {
        ".L": "GBP",
        ".PA": "EUR",
        ".TO": "CAD",
        ".MX": "MXN",
        ".T": "JPY",
    }

    for suffix, currency in suffix_currency_map.items():
        if ticker.endswith(suffix):
            return currency

    return "USD"


def expected_fx_ticker(currency: str) -> str | None:
    """
    Ticker FX esperado en yfinance para convertir a USD.
    Si la moneda ya es USD, no se requiere conversión.
    """
    if currency == "USD":
        return None

    fx_map = {
        "EUR": "EURUSD=X",
        "GBP": "GBPUSD=X",
        "CAD": "CADUSD=X",
        "MXN": "MXNUSD=X",
        "JPY": "JPYUSD=X",
    }

    return fx_map.get(currency)


def recommended_benchmark(asset_type: str) -> str:
    benchmark_map = {
        "renta_variable": "ACWI",
        "etf_global": "ACWI",
        "etf_sectorial": "SPY",
        "renta_fija": "AGG",
        "efectivo_o_corto_plazo": "SHY",
        "commodity": "PDBC",
    }

    return benchmark_map.get(asset_type, "ACWI")


def benchmark_description(asset_type: str) -> str:
    description_map = {
        "renta_variable": "MSCI ACWI ETF como referencia global de renta variable internacional.",
        "etf_global": "MSCI ACWI ETF como referencia global para exposición accionaria diversificada.",
        "etf_sectorial": "SPY como referencia amplia del mercado accionario estadounidense.",
        "renta_fija": "AGG como referencia agregada de bonos investment grade en USD.",
        "efectivo_o_corto_plazo": "SHY como referencia de bonos del Tesoro de corto plazo.",
        "commodity": "PDBC como referencia amplia de materias primas.",
    }

    return description_map.get(asset_type, "Benchmark global de referencia.")


def build_perri_universe() -> dict:
    if not CACHE_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró roboadvisor_cache.csv en: {CACHE_PATH}"
        )

    df = pd.read_csv(CACHE_PATH, index_col=0)
    tickers = sorted({str(col).strip().upper() for col in df.columns if str(col).strip()})

    assets = []

    for ticker in tickers:
        currency = expected_currency(ticker)
        asset_type = classify_asset(ticker)
        benchmark = recommended_benchmark(asset_type)

        assets.append(
            {
                "ticker": ticker,
                "name": ticker,
                "tipo_activo": asset_type,
                "moneda_origen": currency,
                "fx_ticker": expected_fx_ticker(currency),
                "benchmark_ticker": benchmark,
                "benchmark_descripcion": benchmark_description(asset_type),
                "incluir_en_perri": True,
                "fuente": "roboadvisor_cache.csv",
            }
        )

    return {
        "nombre": "Universo institucional de Perri",
        "version": "1.1.0",
        "base_currency": "USD",
        "history_years": 5,
        "conversion_policy": (
            "Los precios deben conservar cierre original y cierre convertido a USD "
            "usando tasa FX histórica diaria cuando el activo no esté denominado en USD."
        ),
        "classification_policy": (
            "Clasificación inicial por listas explícitas de tickers para ETFs de renta fija, "
            "commodities, ETFs sectoriales, ETFs globales y renta variable."
        ),
        "benchmark_policy": (
            "Cada activo tiene un benchmark recomendado según su clase. "
            "Los portafolios mixtos deben compararse contra un benchmark compuesto ponderado "
            "por la asignación a renta variable, renta fija, commodities y liquidez."
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": "roboadvisor_cache.csv",
        "total_assets": len(assets),
        "assets": assets,
    }


def main() -> None:
    universe = build_perri_universe()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(universe, file, ensure_ascii=False, indent=2)

    print(f"OK: JSON creado en {OUTPUT_PATH}")
    print(f"OK: activos registrados: {universe['total_assets']}")

    by_type: dict[str, int] = {}

    for asset in universe["assets"]:
        asset_type = asset["tipo_activo"]
        by_type[asset_type] = by_type.get(asset_type, 0) + 1

    print("OK: clasificación por tipo de activo:")
    for asset_type, count in sorted(by_type.items()):
        print(f"  - {asset_type}: {count}")


if __name__ == "__main__":
    main()
