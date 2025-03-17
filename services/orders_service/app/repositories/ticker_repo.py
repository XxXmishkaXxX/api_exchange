from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.models.ticker import Ticker 


class TickerRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def get_ticker_by_id(self, ticker_id: int) -> Optional[Ticker]:
        result = await self.db.execute(select(Ticker).filter(Ticker.id == ticker_id))
        return result.scalars().first()

    async def get_ticker_by_symbol(self, symbol: str) -> Optional[Ticker]:
        result = await self.db.execute(select(Ticker).filter(Ticker.symbol == symbol))
        return result.scalars().first()
    
    async def create(self, ticker: Ticker):
        try:
            self.db.add(ticker)
            await self.db.commit()
            await self.db.refresh(ticker)
            return ticker 
        except IntegrityError:
            await self.db.rollback()
            raise ValueError(f"Такой тикер уже существует")
        
    async def delete(self, ticker_id: int) -> Optional[Ticker]:
        result = await self.db.execute(select(Ticker).filter(Ticker.id == ticker_id))
        db_ticker = result.scalars().first()
        if db_ticker:
            await self.db.delete(db_ticker)
            await self.db.commit()
        return db_ticker

