from __future__ import annotations

from datetime import datetime

from arch import data
import requests
import pandas as pd
import yfinance as yf

from app.core.settings import Settings


class MacroClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _get_last_close(self, ticker: str) -> float | None:
        df = yf.download(
            ticker,
            period="1mo",
            interval="1d",
            auto_adjust=False,
            progress=False,
            actions=False,
            threads=False,
            timeout=self.settings.macro_timeout_seconds,
        )

        if df is None or df.empty or "Close" not in df.columns:
            return None

        out = df.copy()
        if isinstance(out.columns, pd.MultiIndex):
            level0 = out.columns.get_level_values(0)
            out.columns = level0

        close = pd.to_numeric(out["Close"], errors="coerce").dropna()
        if close.empty:
            return None

        return float(close.iloc[-1])

    def get_us_inflation_yoy_pct(self) -> float | None:
        """
        Calcula inflación anual de EE. UU. usando CPIAUCSL desde FRED.

        Retorna:
            Inflación YoY en porcentaje, por ejemplo 3.25 para 3.25%.
            None si no hay FRED_API_KEY o si FRED no responde.
        """
        api_key = getattr(self.settings, "fred_api_key", None)

        if not api_key:
            return None

        url = "https://api.stlouisfed.org/fred/series/observations"

        params = {
            "series_id": "CPIAUCSL",
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 24,
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.settings.external_api_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except Exception:
            return None

        observations = data.get("observations", [])
        rows = []

        for obs in observations:
            value = obs.get("value")
            date = obs.get("date")

            if value in (None, ".") or date is None:
                continue

            try:
                rows.append(
                    {
                        "date": pd.to_datetime(date),
                        "value": float(value),
                    }
                )
            except Exception:
                continue

        df = pd.DataFrame(rows)

        if df.empty or len(df) < 13:
            return None

        df = df.sort_values("date").reset_index(drop=True)

        current_cpi = float(df["value"].iloc[-1])
        cpi_12m_ago = float(df["value"].iloc[-13])

        if cpi_12m_ago == 0:
            return None

        inflation_yoy_pct = ((current_cpi / cpi_12m_ago) - 1.0) * 100.0
        return float(inflation_yoy_pct)

    def get_us_inflation_yoy_pct(self) -> float | None:
        """
        Calcula inflación anual de EE. UU. usando CPIAUCSL desde FRED.

        Retorna:
            Inflación YoY en porcentaje. Ejemplo: 3.25 significa 3.25%.
            None si no hay FRED_API_KEY o si FRED no responde.
        """
        api_key = getattr(self.settings, "fred_api_key", None)

        if not api_key:
            return None

        url = "https://api.stlouisfed.org/fred/series/observations"

        params = {
            "series_id": "CPIAUCSL",
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 24,
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=getattr(self.settings, "external_api_timeout_seconds", 20),
            )
            response.raise_for_status()
            data = response.json()
        except Exception:
            return None

        observations = data.get("observations", [])
        rows = []

        for obs in observations:
            value = obs.get("value")
            date = obs.get("date")

            if value in (None, ".") or date is None:
                continue

            try:
                rows.append(
                    {
                        "date": pd.to_datetime(date),
                        "value": float(value),
                    }
                )
            except Exception:
                continue
            except Exception:
                continue

        df = pd.DataFrame(rows)

        if df.empty or len(df) < 13:
            return None

        df = df.sort_values("date").reset_index(drop=True)

        current_cpi = float(df["value"].iloc[-1])
        cpi_12m_ago = float(df["value"].iloc[-13])

        if cpi_12m_ago == 0:
            return None

        inflation_yoy_pct = ((current_cpi / cpi_12m_ago) - 1.0) * 100.0

        return float(inflation_yoy_pct)

    def get_macro_snapshot(self, base_currency: str) -> dict:
        base_currency = base_currency.upper()

        if base_currency == "USD":
            rf_ticker = self.settings.rf_ticker_usd.strip()
            note = "Rf basada en USD usando yfinance."
        elif base_currency == "EUR":
            rf_ticker = self.settings.rf_ticker_eur.strip()
            note = "Rf basada en EUR usando yfinance."
        else:
            rf_ticker = self.settings.rf_ticker_cop_proxy.strip()
            note = "COP usa proxy de Rf en USD por restricciones actuales de fuente/tokens."

        rf_value = self._get_last_close(rf_ticker)
        usdcop_value = self._get_last_close("USDCOP=X")

        inflation_yoy = None
        inflation_source = None

        if base_currency == "USD":
            inflation_yoy = self.get_us_inflation_yoy_pct()
            inflation_source = "FRED CPIAUCSL" if inflation_yoy is not None else None

        return {
            "base_currency": base_currency,
            "benchmark_ticker": self.settings.global_benchmark,
            "rf_ticker": rf_ticker,
            "risk_free_rate_pct": rf_value,
            "rf_rate_pct": rf_value,
            "inflation_yoy": inflation_yoy,
            "inflation_pct": inflation_yoy,
            "inflation_source": inflation_source,
            "cop_per_usd": usdcop_value,
            "usdcop_market": usdcop_value,
            "fx_spot": usdcop_value,
            "source": "yfinance + FRED" if inflation_source else "yfinance",
            "note": note,
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }