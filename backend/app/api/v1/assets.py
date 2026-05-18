from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session


from app.core.assets_registry import ALL_ASSETS, MAX_ASSETS_ALLOWED
from app.core.dependencies import get_assets_service, get_db
from app.core.settings import get_settings
from app.schemas.common import AssetSearchResponse, AssetUniverseItem, AssetUniverseResponse
from app.services.assets_service import AssetsService

router = APIRouter()


@router.get("/", summary="Listar universo de activos", response_model=AssetUniverseResponse)
async def list_assets(
    service: AssetsService = Depends(get_assets_service),
    db: Session = Depends(get_db),
) -> AssetUniverseResponse:
    settings = get_settings()
    result = service.list_assets(db=db)

    return AssetUniverseResponse(
        max_assets_allowed=MAX_ASSETS_ALLOWED,
        benchmark_ticker=settings.global_benchmark,
        base_currencies=["USD", "EUR", "COP"],
        assets=[AssetUniverseItem(**item) for item in result],
    )


@router.get("/search", summary="Buscar activos por nombre o ticker", response_model=AssetSearchResponse)
async def search_assets(
    q: str = Query(default="", min_length=0, max_length=30),
    service: AssetsService = Depends(get_assets_service),
    db: Session = Depends(get_db),
) -> AssetSearchResponse:
    result = service.search_assets(query=q, db=db)
    return AssetSearchResponse(
        query=result["query"],
        total_matches=result["total_matches"],
        assets=[AssetUniverseItem(**item) for item in result["assets"]],
    )