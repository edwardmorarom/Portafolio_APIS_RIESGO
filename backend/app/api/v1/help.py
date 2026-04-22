from fastapi import APIRouter, Depends

from app.core.dependencies import get_help_service
from app.schemas.help import HelpCatalogResponse, HelpItem
from app.services.help_service import HelpService

router = APIRouter()


@router.get("/catalog", summary="Catalogo de ayudas para tooltips", response_model=HelpCatalogResponse)
async def get_help_catalog(
    service: HelpService = Depends(get_help_service),
) -> HelpCatalogResponse:
    result = service.get_catalog()
    return HelpCatalogResponse(
        total_items=result["total_items"],
        items=[HelpItem(**item) for item in result["items"]],
    )