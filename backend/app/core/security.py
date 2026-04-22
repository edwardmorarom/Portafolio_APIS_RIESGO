from __future__ import annotations

from fastapi import Header

from app.core.exceptions import InvalidApiKeyError
from app.core.settings import get_settings


def require_internal_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    expected = settings.internal_api_key

    if not expected:
        return

    if x_api_key != expected:
        raise InvalidApiKeyError()