from __future__ import annotations

DEFAULT_ASSETS = [
    {"name": "BP", "ticker": "BP.L", "country": "Reino Unido", "default": True},
    {"name": "Carrefour", "ticker": "CA.PA", "country": "Francia", "default": True},
    {"name": "Couche-Tard", "ticker": "ATD.TO", "country": "Canadá", "default": True},
    {"name": "FEMSA", "ticker": "FEMSAUBD.MX", "country": "México", "default": True},
    {"name": "Seven & i", "ticker": "3382.T", "country": "Japón", "default": True},
]

EXTRA_ASSETS = [
    {"name": "Apple", "ticker": "AAPL", "country": "Estados Unidos", "default": False},
    {"name": "Microsoft", "ticker": "MSFT", "country": "Estados Unidos", "default": False},
    {"name": "Nestle", "ticker": "NESN.SW", "country": "Suiza", "default": False},
    {"name": "Toyota", "ticker": "7203.T", "country": "Japón", "default": False},
    {"name": "Santander", "ticker": "SAN", "country": "España", "default": False},
    {"name": "Shell", "ticker": "SHEL", "country": "Reino Unido", "default": False},
    {"name": "Exxon Mobil", "ticker": "XOM", "country": "Estados Unidos", "default": False},
    {"name": "Coca-Cola FEMSA", "ticker": "KOF", "country": "México", "default": False},
    {"name": "Walmart", "ticker": "WMT", "country": "Estados Unidos", "default": False},
    {"name": "Visa", "ticker": "V", "country": "Estados Unidos", "default": False},
]

ALL_ASSETS = DEFAULT_ASSETS + EXTRA_ASSETS
MAX_ASSETS_ALLOWED = 15