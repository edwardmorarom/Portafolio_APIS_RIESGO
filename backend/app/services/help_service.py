from app.core.help_catalog import HELP_CATALOG


class HelpService:
    def get_catalog(self) -> dict:
        items = [
            {"key": key, "general": value["general"], "estadistico": value["estadistico"]}
            for key, value in HELP_CATALOG.items()
        ]
        return {"total_items": len(items), "items": items}