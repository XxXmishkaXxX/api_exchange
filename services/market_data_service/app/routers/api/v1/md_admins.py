from fastapi import APIRouter, Depends, Path
from typing import List, Annotated


from app.deps.security import admin_required
from app.schemas.asset import AssetSchema
from app.services.assets import AssetsService
from app.deps.services import get_assets_service


router = APIRouter()

@router.post("/instrument")
async def create_instrument(
    asset: Annotated[AssetSchema, Depends()],
    user_info: Annotated[dict, Depends(admin_required)],
    service: Annotated[AssetsService, Depends(get_assets_service)]
):
    return await service.create_asset(asset)


@router.delete("/instrument/{ticker}")
async def remove_instrument(
    ticker: Annotated[str, Path(description="Тикер актива")],
    user_info: Annotated[dict, Depends(admin_required)],
    service: Annotated[AssetsService, Depends(get_assets_service)]
):
    return await service.remove_asset(ticker)
