from fastapi import APIRouter

from app.schemas.common import AssetItem, AssetsResponse

router = APIRouter()


@router.get("/", summary="Listar activos disponibles", response_model=AssetsResponse)
async def list_assets() -> AssetsResponse:
    return AssetsResponse(
        assets=[
            AssetItem(name="Seven & i Holdings", ticker="3382.T", country="Japón"),
            AssetItem(name="Alimentation Couche-Tard", ticker="ATD.TO", country="Canadá"),
            AssetItem(name="FEMSA", ticker="FEMSAUBD.MX", country="México"),
            AssetItem(name="BP", ticker="BP.L", country="Reino Unido"),
            AssetItem(name="Carrefour", ticker="CA.PA", country="Francia"),
        ]
    )