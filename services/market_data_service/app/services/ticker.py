from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.schemas.ticker import TickerSchema
from app.repositories.ticker_repo import TickerRepository
from app.models.ticker import Ticker
from app.db.database import get_db

class TickerService:

    def __init__(self, ticker_repo: TickerRepository) -> None:
        self.repo = ticker_repo

    async def create_ticker(self, ticker: TickerSchema) -> dict:

        try:
            ticker = Ticker.from_orm(ticker) 
            await self.repo.create(ticker)

            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
        
    async def remove_ticker(self, ticker_symbol: str) -> dict:

        try:
            await self.repo.delete(ticker_symbol)

            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
        

def get_ticker_service(
    session: AsyncSession = Depends(get_db)
    ):
    return TickerService(ticker_repo=TickerRepository(session))