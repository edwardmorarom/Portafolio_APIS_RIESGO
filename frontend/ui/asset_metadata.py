from __future__ import annotations

from typing import Any


US_TICKERS = {
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "CSCO", "ADBE",
    "CRM", "NFLX", "INTC", "AMD", "TXN", "QCOM", "IBM", "NOW", "UBER", "INTU",
    "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "AXP", "V", "MA", "SCHW", "SPGI",
    "PYPL", "CME", "CB", "PGR", "MMC", "AON", "ICE", "VTR", "JNJ", "UNH", "LLY",
    "MRK", "ABBV", "PFE", "TMO", "DHR", "ABT", "BMY", "AMGN", "CVS", "SYK", "ISRG",
    "MDT", "GILD", "VRTX", "REGN", "HUM", "BSX", "WMT", "PG", "KO", "PEP", "COST",
    "MCD", "HD", "NKE", "SBUX", "TGT", "LOW", "SYY", "PM", "MO", "EL", "CL", "KMB",
    "MDLZ", "TJX", "BKNG", "XOM", "CVX", "COP", "SLB", "EOG", "UNP", "HON", "UPS",
    "LMT", "BA", "CAT", "GE", "MMM", "DE", "RTX", "NOC", "GD", "LIN", "SHW", "ECL",
    "AMT", "PLD", "CCI", "EQIX", "PSA", "O", "SPG", "WELL", "DLR",
}

INTERNATIONAL_TICKER_COUNTRIES = {
    "TSM": "Taiwán",
    "ASML": "Países Bajos",
    "NVO": "Dinamarca",
    "NVS": "Suiza",
    "SAP": "Alemania",
    "TM": "Japón",
    "BABA": "China",
    "BHP": "Australia",
    "RIO": "Reino Unido / Australia",
    "SNY": "Francia",
    "AZN": "Reino Unido",
    "HSBC": "Reino Unido",
    "UL": "Reino Unido",
    "TD": "Canadá",
    "RY": "Canadá",
    "SONY": "Japón",
    "IBN": "India",
    "HDB": "India",
    "BUD": "Bélgica",
    "DEO": "Reino Unido",
    "3382.T": "Japón",
    "ATD.TO": "Canadá",
    "FEMSAUBD.MX": "México",
    "BP.L": "Reino Unido",
    "CA.PA": "Francia",
    "NESN.SW": "Suiza",
    "7203.T": "Japón",
    "SAN": "España",
    "SHEL": "Reino Unido",
    "KOF": "México",
}

ETF_COUNTRIES = {
    "AGG": "Estados Unidos - renta fija",
    "BND": "Estados Unidos - renta fija",
    "TLT": "Estados Unidos - bonos Tesoro",
    "IEF": "Estados Unidos - bonos Tesoro",
    "SHY": "Estados Unidos - bonos Tesoro",
    "LQD": "Estados Unidos - crédito corporativo",
    "HYG": "Estados Unidos - high yield",
    "JNK": "Estados Unidos - high yield",
    "BNDX": "Global ex Estados Unidos - renta fija",
    "EMB": "Mercados emergentes - deuda",
    "MUB": "Estados Unidos - bonos municipales",
    "TIP": "Estados Unidos - bonos inflación",
    "GOVT": "Estados Unidos - bonos Tesoro",
    "VCIT": "Estados Unidos - crédito corporativo",
    "BSV": "Estados Unidos - renta fija corta",
    "VCSH": "Estados Unidos - crédito corto",
    "IGSB": "Estados Unidos - crédito corto",
    "SPIP": "Estados Unidos - bonos inflación",
    "FLOT": "Estados Unidos - tasa flotante",
    "BKLN": "Estados Unidos - préstamos senior",
    "SPY": "Estados Unidos - mercado amplio",
    "QQQ": "Estados Unidos - Nasdaq 100",
    "DIA": "Estados Unidos - Dow Jones",
    "IWM": "Estados Unidos - small caps",
    "VTI": "Estados Unidos - mercado total",
    "VEA": "Mercados desarrollados ex Estados Unidos",
    "VWO": "Mercados emergentes",
    "EEM": "Mercados emergentes",
    "EFA": "Mercados desarrollados ex Estados Unidos",
    "XLF": "Estados Unidos - sector financiero",
    "XLV": "Estados Unidos - sector salud",
    "XLK": "Estados Unidos - sector tecnología",
    "XLE": "Estados Unidos - sector energía",
    "XLI": "Estados Unidos - sector industrial",
    "XLP": "Estados Unidos - consumo básico",
    "XLY": "Estados Unidos - consumo discrecional",
    "XLU": "Estados Unidos - utilities",
    "XLB": "Estados Unidos - materiales",
    "XLRE": "Estados Unidos - real estate",
    "ARKK": "Estados Unidos - innovación",
    "VNQ": "Estados Unidos - real estate",
    "GLD": "Global - oro",
    "SLV": "Global - plata",
    "IAU": "Global - oro",
    "PDBC": "Global - materias primas",
    "USO": "Estados Unidos - petróleo",
    "UNG": "Estados Unidos - gas natural",
    "DBA": "Global - agricultura",
    "WEAT": "Global - trigo",
    "CORN": "Global - maíz",
    "CPER": "Global - cobre",
}

COUNTRY_ALIASES = {
    "JP": "Japón",
    "CA": "Canadá",
    "MX": "México",
    "UK": "Reino Unido",
    "GB": "Reino Unido",
    "FR": "Francia",
    "US": "Estados Unidos",
    "USA": "Estados Unidos",
    "UNITED STATES": "Estados Unidos",
    "GLOBAL / US-LISTED": "",
    "N/D": "",
}


def display_country(asset: dict[str, Any]) -> str:
    ticker = str(asset.get("ticker", "")).strip().upper()
    raw_country = str(asset.get("country", "") or "").strip()
    normalized = raw_country.upper()

    if normalized in COUNTRY_ALIASES:
        aliased = COUNTRY_ALIASES[normalized]
        if aliased:
            return aliased

    if raw_country and normalized not in {"GLOBAL / US-LISTED", "N/D"}:
        return raw_country

    if ticker in INTERNATIONAL_TICKER_COUNTRIES:
        return INTERNATIONAL_TICKER_COUNTRIES[ticker]
    if ticker in ETF_COUNTRIES:
        return ETF_COUNTRIES[ticker]
    if ticker in US_TICKERS:
        return "Estados Unidos"

    return "N/D"
