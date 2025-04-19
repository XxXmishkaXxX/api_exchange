from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.models.asset import Asset 



class AssetRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self, ):
        result = await self.session.execute(select(Asset))
        return result.scalars().all()

    async def get_asset_by_id(self, asset_id: int) -> Optional[Asset]:
        result = await self.session.execute(select(Asset).filter(Asset.id == asset_id))
        return result.scalars().first()
    
    async def get_asset_by_ticker(self, ticker: str) -> Optional[Asset]:
        result = await self.session.execute(select(Asset).filter(Asset.ticker == ticker))
        return result.scalars().first()

    async def create(self, asset: Asset):
        try:
            self.session.add(asset)
            await self.session.commit()
            await self.session.refresh(asset)
            return asset 
        except IntegrityError:
            await self.session.rollback()
            raise ValueError(f"Такой тикер уже существует")
        
    async def delete(self, ticker: str) -> Optional[Asset]:
        result = await self.session.execute(select(Asset).filter(Asset.ticker == ticker))
        db_ticker = result.scalars().first()
        if db_ticker:
            await self.session.delete(db_ticker)
            await self.session.commit()
        return db_ticker
