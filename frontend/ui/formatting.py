from __future__ import annotations

from typing import Any

import streamlit as st


DEFAULT_DECIMALS = 2
MAX_DECIMALS = 6


def get_decimal_places(default: int = DEFAULT_DECIMALS) -> int:
    value = st.session_state.get("display_decimals", default)
    try:
        decimals = int(value)
    except (TypeError, ValueError):
        decimals = default
    return min(max(decimals, 0), MAX_DECIMALS)


def format_number(value: Any, decimals: int | None = None) -> str:
    try:
        precision = get_decimal_places() if decimals is None else int(decimals)
        return f"{float(value):,.{precision}f}"
    except Exception:
        return "N/D"


def format_percent(value: Any, decimals: int | None = None, *, already_pct: bool = False) -> str:
    try:
        precision = get_decimal_places() if decimals is None else int(decimals)
        numeric = float(value)
        if not already_pct:
            numeric *= 100.0
        return f"{numeric:,.{precision}f}%"
    except Exception:
        return "N/D"


def format_money(value: Any, decimals: int | None = None) -> str:
    try:
        precision = get_decimal_places() if decimals is None else int(decimals)
        return f"${float(value):,.{precision}f}"
    except Exception:
        return "N/D"


def decimal_format() -> str:
    return "%." + str(get_decimal_places()) + "f"
