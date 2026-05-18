from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.assets_registry import ALL_ASSETS
from app.db.models import Asset


class AssetsService:
    def _asset_to_item(self, asset: Asset, default_tickers: set[str]) -> dict:
        return {
            "name": asset.name or asset.ticker,
            "ticker": asset.ticker,
            "country": asset.country or "N/D",
            "default": asset.ticker in default_tickers,
        }

    def _fallback_assets(self) -> list[dict]:
        return list(ALL_ASSETS)

    def list_assets(self, db: Session | None = None) -> list[dict]:
        """
        Lista activos desde SQLite.
        Si la base no tiene activos cargados, usa el registro estático como respaldo.
        """
        if db is None:
            return self._fallback_assets()

        default_tickers = {asset["ticker"] for asset in ALL_ASSETS if asset.get("default") is True}

        assets = list(
            db.scalars(
                select(Asset).order_by(Asset.ticker.asc())
            )
        )

        if not assets:
            return self._fallback_assets()

        return [
            self._asset_to_item(asset, default_tickers=default_tickers)
            for asset in assets
        ]

    def search_assets(self, query: str, db: Session | None = None) -> dict:
        q = query.strip().lower()
        assets = self.list_assets(db=db)

        if not q:
            results = assets
        else:
            results = [
                asset
                for asset in assets
                if q in asset["ticker"].lower() or q in asset["name"].lower()
            ]

        results = sorted(
            results,
            key=lambda x: (
                not x["ticker"].lower().startswith(q) if q else False,
                not x["name"].lower().startswith(q) if q else False,
                x["default"] is False,
                x["name"],
            ),
        )

        return {
            "query": query,
            "total_matches": len(results),
            "assets": results,
        }