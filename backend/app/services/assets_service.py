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
            "asset_type": asset.asset_type,
            "benchmark_ticker": asset.benchmark_ticker,
            "benchmark_description": asset.benchmark_description,
            "include_in_perri": asset.include_in_perri,
            "source": asset.source,
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

    def summarize_assets(self, db: Session) -> dict:
        assets = list(db.scalars(select(Asset)))

        by_asset_type: dict[str, int] = {}
        by_benchmark: dict[str, int] = {}
        perri_assets = 0

        for asset in assets:
            asset_type = asset.asset_type or "sin_clasificar"
            benchmark = asset.benchmark_ticker or "sin_benchmark"

            by_asset_type[asset_type] = by_asset_type.get(asset_type, 0) + 1
            by_benchmark[benchmark] = by_benchmark.get(benchmark, 0) + 1

            if asset.include_in_perri:
                perri_assets += 1

        return {
            "total_assets": len(assets),
            "perri_assets": perri_assets,
            "by_asset_type": dict(sorted(by_asset_type.items())),
            "by_benchmark": dict(sorted(by_benchmark.items())),
        }