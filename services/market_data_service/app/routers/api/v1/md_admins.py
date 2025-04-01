from fastapi import APIRouter, Depends


from app.deps.security import admin_required
from app.schemas.ticker import TickerSchema
from app.services.ticker import TickerService, get_ticker_service
from app.services.producer import KafkaProducerService, get_producer_service


router = APIRouter()


@router.post("/instrument")
async def create_instrument(ticker: TickerSchema,
                          user_info: dict = Depends(admin_required),
                          service: TickerService = Depends(get_ticker_service),
                          prod: KafkaProducerService = Depends(get_producer_service)):
    return await service.create_ticker(ticker, prod)


@router.delete("/instrument/{ticker}")
async def remove_instrument(ticker: str,
                          user_info: dict = Depends(admin_required),
                          service: TickerService = Depends(get_ticker_service),
                          prod: KafkaProducerService = Depends(get_producer_service)):
    return await service.remove_ticker(ticker, prod)