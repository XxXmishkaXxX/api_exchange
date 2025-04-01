from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.schemas.ticker import TickerSchema
from app.repositories.ticker_repo import TickerRepository
from app.services.producer import KafkaProducerService
from app.models.ticker import Ticker
from app.db.database import get_db

class TickerService:

    def __init__(self, ticker_repo: TickerRepository) -> None:
        self.repo = ticker_repo

    async def create_ticker(self, ticker: TickerSchema, producer: KafkaProducerService) -> dict:

        try:
            ticker_data = ticker.model_dump()
            ticker = await self.repo.create(Ticker(**ticker_data) )
            
            data = {
                "action": "ADD",
                "ticker_id": ticker.id,
                "name": ticker.name,
                "symbol": ticker.symbol
            }
            await producer.send_message(data)

            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
        
    async def remove_ticker(self, ticker_symbol: str, producer: KafkaProducerService) -> dict:

        try:
            ticker = await self.repo.delete(ticker_symbol)

            data = {
                "action": "REMOVE",
                "ticker_id": ticker.id
            }
            await producer.send_message(data)

            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
        

def get_ticker_service(
    session: AsyncSession = Depends(get_db)
    ):
    return TickerService(ticker_repo=TickerRepository(session))