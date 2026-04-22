from __future__ import annotations

from app.core.assets_registry import ALL_ASSETS


class AssetsService:
    def search_assets(self, query: str) -> dict:
        q = query.strip().lower()

        if not q:
            results = ALL_ASSETS
        else:
            results = [
                asset
                for asset in ALL_ASSETS
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