from fastapi import APIRouter, Depends


from app.core.config import settings
from app.deps.security import admin_required
from app.schemas.ticker import TickerSchema
from app.services.ticker import TickerService, get_ticker_service


router = APIRouter()



@router.get("/instrumet")
async def create_instrument(ticker: TickerSchema,
                          user_info: dict = Depends(admin_required),
                          service: TickerService = Depends(get_ticker_service)):
    return await service.create_ticker(ticker)


@router.delete("/instrumet/{ticker}")
async def remove_instrument(ticker_symbol: str,
                          user_info: dict = Depends(admin_required),
                          service: TickerService = Depends(get_ticker_service)):
    return await service.remove_ticker(ticker_symbol)