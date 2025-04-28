from fastapi import APIRouter, Depends, Path
from typing import List, Annotated


from app.deps.security import admin_required
from app.schemas.asset import AssetSchema
from app.services.assets import AssetsService, get_assets_service
from app.services.producer import KafkaProducerService, get_producer_service


router = APIRouter()

@router.post("/instrument")
async def create_instrument(
    asset: Annotated[AssetSchema, Depends()],
    user_info: Annotated[dict, Depends(admin_required)],
    service: Annotated[AssetsService, Depends(get_assets_service)],
    prod: Annotated[KafkaProducerService, Depends(get_producer_service)]
):
    return await service.create_asset(asset, prod)


@router.delete("/instrument/{ticker}")
async def remove_instrument(
    ticker: Annotated[str, Path(description="Тикер актива")],
    user_info: Annotated[dict, Depends(admin_required)],
    service: Annotated[AssetsService, Depends(get_assets_service)],
    prod: Annotated[KafkaProducerService, Depends(get_producer_service)]
):
    return await service.remove_asset(ticker, prod)
