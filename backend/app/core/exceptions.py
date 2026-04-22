from __future__ import annotations

from app.core.error_catalog import ERROR_CATALOG


class AppBaseException(Exception):
    def __init__(self, catalog_key: str, extra: dict | None = None) -> None:
        if catalog_key not in ERROR_CATALOG:
            raise ValueError(f"Catalog key no existe: {catalog_key}")

        payload = ERROR_CATALOG[catalog_key]
        self.catalog_key = catalog_key
        self.status_code = payload["status_code"]
        self.error_code = payload["error_code"]
        self.message = payload["message"]
        self.extra = extra or {}
        super().__init__(self.message)


class InvalidDateRangeError(AppBaseException):
    def __init__(self) -> None:
        super().__init__("INVALID_DATE_RANGE")


class FutureDateError(AppBaseException):
    def __init__(self) -> None:
        super().__init__("FUTURE_DATE")


class InvalidApiKeyError(AppBaseException):
    def __init__(self) -> None:
        super().__init__("INVALID_API_KEY")


class TickerNotFoundError(AppBaseException):
    def __init__(self, ticker: str | None = None) -> None:
        super().__init__("TICKER_NOT_FOUND", extra={"ticker": ticker} if ticker else None)


class InsufficientObsVarError(AppBaseException):
    def __init__(self, required: int | None = None) -> None:
        super().__init__("INSUFFICIENT_OBS_VAR", extra={"required": required} if required is not None else None)


class InsufficientObsCapmError(AppBaseException):
    def __init__(self, required: int | None = None) -> None:
        super().__init__("INSUFFICIENT_OBS_CAPM", extra={"required": required} if required is not None else None)


class InsufficientObsPortfolioError(AppBaseException):
    def __init__(self, required: int | None = None) -> None:
        super().__init__("INSUFFICIENT_OBS_PORTFOLIO", extra={"required": required} if required is not None else None)


class ExternalApiFailureError(AppBaseException):
    def __init__(self, source: str | None = None) -> None:
        super().__init__("EXTERNAL_API_FAILURE", extra={"source": source} if source else None)