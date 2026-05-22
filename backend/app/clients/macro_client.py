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

    def _fred_latest_value(self, series_id: str) -> dict | None:
        api_key = getattr(self.settings, "fred_api_key", None)
        if not api_key:
            return None

        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 10,
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=getattr(self.settings, "external_api_timeout_seconds", 20),
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return None

        for obs in payload.get("observations", []):
            value = obs.get("value")
            obs_date = obs.get("date")
            if value in (None, ".") or not obs_date:
                continue
            try:
                return {
                    "series_id": series_id,
                    "date": obs_date,
                    "value_pct": float(value),
                    "value_decimal": float(value) / 100.0,
                }
            except Exception:
                continue
        return None

    def _fred_observations(self, series_id: str, limit: int = 36) -> list[dict]:
        api_key = getattr(self.settings, "fred_api_key", None)
        if not api_key:
            return []

        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit,
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=getattr(self.settings, "external_api_timeout_seconds", 20),
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        rows: list[dict] = []
        for obs in payload.get("observations", []):
            value = obs.get("value")
            obs_date = obs.get("date")
            if value in (None, ".") or not obs_date:
                continue
            try:
                rows.append({"date": obs_date, "value": float(value)})
            except Exception:
                continue
        return list(reversed(rows))

    def _yfinance_history(self, ticker: str, period: str = "1y") -> list[dict]:
        try:
            df = yf.download(
                ticker,
                period=period,
                interval="1d",
                auto_adjust=False,
                progress=False,
                actions=False,
                threads=False,
                timeout=self.settings.macro_timeout_seconds,
            )
        except Exception:
            return []

        if df is None or df.empty or "Close" not in df.columns:
            return []

        out = df.copy()
        if isinstance(out.columns, pd.MultiIndex):
            out.columns = out.columns.get_level_values(0)

        close = pd.to_numeric(out["Close"], errors="coerce").dropna()
        return [
            {"date": str(idx.date()) if hasattr(idx, "date") else str(idx), "value": float(value)}
            for idx, value in close.tail(252).items()
        ]

    def get_us_treasury_yield_curve(self) -> dict:
        """
        Obtiene puntos de curva Treasury desde FRED para renta fija:
        DGS3MO, DGS1, DGS2, DGS5, DGS10 y DGS30.
        Si no hay API key o FRED falla, retorna puntos metodologicos de fallback
        marcados como no provenientes de FRED para no inventar la fuente.
        """
        fred_points = [
            ("DGS3MO", 0.25),
            ("DGS1", 1.0),
            ("DGS2", 2.0),
            ("DGS5", 5.0),
            ("DGS10", 10.0),
            ("DGS30", 30.0),
        ]

        points: list[dict] = []
        for series_id, maturity_years in fred_points:
            latest = self._fred_latest_value(series_id)
            if latest is None:
                points = []
                break
            points.append(
                {
                    "series_id": series_id,
                    "maturity_years": maturity_years,
                    "rate_pct": latest["value_pct"],
                    "rate_decimal": latest["value_decimal"],
                    "yield_rate": latest["value_decimal"],
                    "yield_pct": latest["value_pct"],
                    "date": latest["date"],
                }
            )

        if points:
            return {
                "source": "FRED",
                "fallback": False,
                "points": points,
                "message": "Curva Treasury cargada desde FRED.",
            }

        fallback = [
            ("DGS3MO", 0.25, 0.030),
            ("DGS1", 1.0, 0.034),
            ("DGS2", 2.0, 0.036),
            ("DGS5", 5.0, 0.039),
            ("DGS10", 10.0, 0.043),
            ("DGS30", 30.0, 0.049),
        ]
        return {
            "source": "fallback_local",
            "fallback": True,
            "points": [
                {
                    "series_id": series_id,
                    "maturity_years": maturity,
                    "rate_pct": rate * 100.0,
                    "rate_decimal": rate,
                    "yield_rate": rate,
                    "yield_pct": rate * 100.0,
                    "date": None,
                }
                for series_id, maturity, rate in fallback
            ],
            "message": "No hay FRED_API_KEY o FRED no respondio; se devuelven puntos locales marcados como fallback.",
        }

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
            note = "Rf USD prioriza FRED DGS3MO; si no esta disponible usa yfinance."
        elif base_currency == "EUR":
            rf_ticker = self.settings.rf_ticker_eur.strip()
            note = "Rf basada en EUR usando yfinance."
        else:
            rf_ticker = self.settings.rf_ticker_cop_proxy.strip()
            note = "COP usa proxy de Rf en USD por restricciones actuales de fuente/tokens."

        fred_rf = self._fred_latest_value("DGS3MO") if base_currency == "USD" else None
        rf_value = fred_rf["value_pct"] if fred_rf is not None else self._get_last_close(rf_ticker)
        usdcop_value = self._get_last_close("USDCOP=X")
        rf_history = self._fred_observations("DGS3MO", limit=252) if base_currency == "USD" else self._yfinance_history(rf_ticker)
        inflation_history = self._fred_observations("CPIAUCSL", limit=60) if base_currency == "USD" else []
        usdcop_history = self._yfinance_history("USDCOP=X")

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
            "indicators": {
                "risk_free_rate": {
                    "series_id": "DGS3MO" if base_currency == "USD" and fred_rf is not None else rf_ticker,
                    "latest_value": rf_value,
                    "latest_date": fred_rf["date"] if fred_rf is not None else None,
                    "history": rf_history,
                    "source": "FRED" if base_currency == "USD" and fred_rf is not None else "yfinance",
                },
                "inflation": {
                    "series_id": "CPIAUCSL" if base_currency == "USD" else None,
                    "latest_value": inflation_yoy,
                    "latest_date": inflation_history[-1]["date"] if inflation_history else None,
                    "history": inflation_history,
                    "source": inflation_source,
                },
                "usdcop": {
                    "series_id": "USDCOP=X",
                    "latest_value": usdcop_value,
                    "latest_date": usdcop_history[-1]["date"] if usdcop_history else None,
                    "history": usdcop_history,
                    "source": "yfinance",
                },
            },
            "source": "FRED + yfinance" if (inflation_source or fred_rf is not None) else "yfinance",
            "note": note,
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
