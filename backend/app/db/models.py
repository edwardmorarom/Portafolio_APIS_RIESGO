from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    market: Mapped[str | None] = mapped_column(String(80), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)

    asset_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    benchmark_ticker: Mapped[str | None] = mapped_column(String(20), nullable=True)
    benchmark_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    include_in_perri: Mapped[bool] = mapped_column(default=False, nullable=False)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    prices: Mapped[list["Price"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
    )


class Price(Base):
    """
    Precio histórico diario orientado a análisis de riesgo.

    Se guarda únicamente el cierre:
    - close_original: cierre en moneda original del activo.
    - original_currency: moneda original del precio.
    - fx_rate_to_usd: tasa histórica usada para convertir a USD.
    - close_usd: cierre convertido a USD.
    - close: campo de compatibilidad, debe guardar el mismo valor de close_usd.
    """

    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    close_original: Mapped[float] = mapped_column(Float, nullable=False)
    original_currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")

    fx_ticker: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fx_rate_to_usd: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    close_usd: Mapped[float] = mapped_column(Float, nullable=False)

    # Compatibilidad temporal con servicios que esperen una columna genérica close.
    # Metodológicamente debe equivaler a close_usd.
    close: Mapped[float] = mapped_column(Float, nullable=False)

    source: Mapped[str] = mapped_column(String(50), nullable=False, default="yfinance")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    asset: Mapped["Asset"] = relationship(back_populates="prices")

    __table_args__ = (
        UniqueConstraint("asset_id", "date", name="uq_prices_asset_date"),
        Index("ix_prices_asset_date", "asset_id", "date"),
        Index("ix_prices_currency", "original_currency"),
    )


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    weights: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PredictionLog(Base):
    __tablename__ = "predictions_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_version: Mapped[str] = mapped_column(String(40), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    input_features: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    prediction: Mapped[float] = mapped_column(Float, nullable=False)
    actual: Mapped[float | None] = mapped_column(Float, nullable=True)


class SignalLog(Base):
    __tablename__ = "signals_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    rule: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    signal: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class MacroCache(Base):
    __tablename__ = "macro_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cache_key: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
