from __future__ import annotations

from typing import Any

import math
import pandas as pd
import streamlit as st


DEFAULT_DECIMALS = 2
MAX_DECIMALS = 6
SCIENTIFIC_SMALL_THRESHOLD = 1e-4
_ORIGINAL_DATAFRAME = None


def get_decimal_places(default: int = DEFAULT_DECIMALS) -> int:
    value = st.session_state.get("display_decimals", default)
    try:
        decimals = int(value)
    except (TypeError, ValueError):
        decimals = default
    return min(max(decimals, 0), MAX_DECIMALS)


def _to_float(value: Any) -> float:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError("Valor no finito")
    return numeric


def _locale_fixed(value: float, precision: int) -> str:
    formatted = f"{value:,.{precision}f}"
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def _format_scientific(value: float, precision: int) -> str:
    text = f"{value:.{min(max(precision, 2), MAX_DECIMALS)}e}"
    mantissa, exponent = text.split("e")
    mantissa = mantissa.rstrip("0").rstrip(".").replace(".", ",")
    exponent_value = int(exponent)
    return f"{mantissa}e{exponent_value}"


def _should_use_scientific(value: float, precision: int) -> bool:
    absolute = abs(value)
    visible_threshold = 10 ** (-max(precision, 0))
    return 0 < absolute < max(SCIENTIFIC_SMALL_THRESHOLD, visible_threshold)


def format_number(value: Any, decimals: int | None = None) -> str:
    try:
        precision = get_decimal_places() if decimals is None else int(decimals)
        numeric = _to_float(value)
        if _should_use_scientific(numeric, precision):
            return _format_scientific(numeric, precision)
        return _locale_fixed(numeric, precision)
    except Exception:
        return "N/D"


def format_percent(value: Any, decimals: int | None = None, *, already_pct: bool = False) -> str:
    try:
        precision = get_decimal_places() if decimals is None else int(decimals)
        numeric = _to_float(value)
        if not already_pct:
            numeric *= 100.0
        if _should_use_scientific(numeric, precision):
            return f"{_format_scientific(numeric, precision)}%"
        return f"{_locale_fixed(numeric, precision)}%"
    except Exception:
        return "N/D"


def format_money(value: Any, decimals: int | None = None) -> str:
    try:
        precision = get_decimal_places() if decimals is None else int(decimals)
        numeric = _to_float(value)
        if _should_use_scientific(numeric, precision):
            return f"${_format_scientific(numeric, precision)}"
        return f"${_locale_fixed(numeric, precision)}"
    except Exception:
        return "N/D"


def decimal_format() -> str:
    return "%." + str(get_decimal_places()) + "f"


def apply_decimal_display_options() -> None:
    precision = get_decimal_places()
    pd.options.display.float_format = lambda value: format_number(value, decimals=precision)


def format_dataframe_for_display(data: Any, decimals: int | None = None) -> Any:
    precision = get_decimal_places() if decimals is None else int(decimals)
    if isinstance(data, pd.DataFrame):
        formatted = data.copy()
        for column in formatted.columns:
            if pd.api.types.is_float_dtype(formatted[column]) or pd.api.types.is_integer_dtype(formatted[column]):
                formatted[column] = formatted[column].map(
                    lambda value: "" if pd.isna(value) else format_number(value, decimals=precision)
                )
        return formatted

    if isinstance(data, pd.Series):
        if pd.api.types.is_float_dtype(data) or pd.api.types.is_integer_dtype(data):
            return data.map(lambda value: "" if pd.isna(value) else format_number(value, decimals=precision))

    return data


def patch_streamlit_dataframe_locale() -> None:
    global _ORIGINAL_DATAFRAME
    if _ORIGINAL_DATAFRAME is not None:
        return

    _ORIGINAL_DATAFRAME = st.dataframe

    def localized_dataframe(data=None, *args, **kwargs):
        return _ORIGINAL_DATAFRAME(format_dataframe_for_display(data), *args, **kwargs)

    st.dataframe = localized_dataframe
