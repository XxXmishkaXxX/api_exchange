from fastapi import APIRouter, Depends


from app.services.market_data import MarketDataService, get_market_data_service



router = APIRouter()


@router.get("/instrument")
async def get_assets_list(service: MarketDataService = Depends(get_market_data_service)):
    return await service.get_list_assets()

