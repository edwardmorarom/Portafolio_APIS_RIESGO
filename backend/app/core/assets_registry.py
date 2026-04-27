from __future__ import annotations

DEFAULT_ASSETS = [
    {
        "name": "BP",
        "ticker": "BP.L",
        "country": "Reino Unido",
        "default": True,
        "currency": "GBP",
        "fx_to_usd": "GBPUSD=X",
        "price_scale": 0.01,  # BP.L suele venir en pence; se convierte a libras antes de USD
    },
    {
        "name": "Carrefour",
        "ticker": "CA.PA",
        "country": "Francia",
        "default": True,
        "currency": "EUR",
        "fx_to_usd": "EURUSD=X",
        "price_scale": 1.0,
    },
    {
        "name": "Couche-Tard",
        "ticker": "ATD.TO",
        "country": "Canadá",
        "default": True,
        "currency": "CAD",
        "fx_to_usd": "CADUSD=X",
        "price_scale": 1.0,
    },
    {
        "name": "FEMSA",
        "ticker": "FEMSAUBD.MX",
        "country": "México",
        "default": True,
        "currency": "MXN",
        "fx_to_usd": "MXNUSD=X",
        "price_scale": 1.0,
    },
    {
        "name": "Seven & i",
        "ticker": "3382.T",
        "country": "Japón",
        "default": True,
        "currency": "JPY",
        "fx_to_usd": "JPYUSD=X",
        "price_scale": 1.0,
    },
]

EXTRA_ASSETS = [
    {
        "name": "Apple",
        "ticker": "AAPL",
        "country": "Estados Unidos",
        "default": False,
        "currency": "USD",
        "fx_to_usd": None,
        "price_scale": 1.0,
    },
    {
        "name": "Microsoft",
        "ticker": "MSFT",
        "country": "Estados Unidos",
        "default": False,
        "currency": "USD",
        "fx_to_usd": None,
        "price_scale": 1.0,
    },
    {
        "name": "Nestle",
        "ticker": "NESN.SW",
        "country": "Suiza",
        "default": False,
        "currency": "CHF",
        "fx_to_usd": "CHFUSD=X",
        "price_scale": 1.0,
    },
    {
        "name": "Toyota",
        "ticker": "7203.T",
        "country": "Japón",
        "default": False,
        "currency": "JPY",
        "fx_to_usd": "JPYUSD=X",
        "price_scale": 1.0,
    },
    {
        "name": "Santander",
        "ticker": "SAN",
        "country": "España",
        "default": False,
        "currency": "USD",
        "fx_to_usd": None,
        "price_scale": 1.0,
    },
    {
        "name": "Shell",
        "ticker": "SHEL",
        "country": "Reino Unido",
        "default": False,
        "currency": "USD",
        "fx_to_usd": None,
        "price_scale": 1.0,
    },
    {
        "name": "Exxon Mobil",
        "ticker": "XOM",
        "country": "Estados Unidos",
        "default": False,
        "currency": "USD",
        "fx_to_usd": None,
        "price_scale": 1.0,
    },
    {
        "name": "Coca-Cola FEMSA",
        "ticker": "KOF",
        "country": "México",
        "default": False,
        "currency": "USD",
        "fx_to_usd": None,
        "price_scale": 1.0,
    },
    {
        "name": "Walmart",
        "ticker": "WMT",
        "country": "Estados Unidos",
        "default": False,
        "currency": "USD",
        "fx_to_usd": None,
        "price_scale": 1.0,
    },
    {
        "name": "Visa",
        "ticker": "V",
        "country": "Estados Unidos",
        "default": False,
        "currency": "USD",
        "fx_to_usd": None,
        "price_scale": 1.0,
    },
]

ALL_ASSETS = DEFAULT_ASSETS + EXTRA_ASSETS
MAX_ASSETS_ALLOWED = 15

ASSET_METADATA_BY_TICKER = {
    asset["ticker"].upper(): asset
    for asset in ALL_ASSETS
}