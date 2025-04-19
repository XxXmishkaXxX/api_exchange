from fastapi import APIRouter, Depends


from app.deps.security import admin_required
from app.schemas.asset import AssetSchema
from app.services.assets import AssetsService, get_assets_service
from app.services.producer import KafkaProducerService, get_producer_service


router = APIRouter()


@router.post("/instrument")
async def create_instrument(asset: AssetSchema,
                          user_info: dict = Depends(admin_required),
                          service: AssetsService = Depends(get_assets_service),
                          prod: KafkaProducerService = Depends(get_producer_service)):
    return await service.create_asset(asset, prod)


@router.delete("/instrument/{ticker}")
async def remove_instrument(ticker: str,
                          user_info: dict = Depends(admin_required),
                          service: AssetsService = Depends(get_assets_service),
                          prod: KafkaProducerService = Depends(get_producer_service)):
    return await service.remove_asset(ticker, prod)