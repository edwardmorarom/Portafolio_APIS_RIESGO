from __future__ import annotations

import pandas as pd

from app.core.exceptions import FutureDateError, InvalidDateRangeError


def normalize_end_date_to_available_data(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    out.index = pd.to_datetime(out.index)
    out = out.sort_index()
    out = out[~out.index.duplicated(keep="last")]
    return out


def validate_not_future(start: str, end: str) -> None:
    start_dt = pd.Timestamp(start).normalize()
    end_dt = pd.Timestamp(end).normalize()
    today = pd.Timestamp.today().normalize()

    if start_dt >= end_dt:
        raise InvalidDateRangeError()
    if end_dt > today:
        raise FutureDateError()