from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, delete
from typing import Optional

from app.models.asset import Asset 


class AssetRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.db = session
    
    async def get_asset_by_ticker(self, ticker: str) -> Asset:
        asset_obj = await self.session.execute(
            select(Asset).where(Asset.ticker == ticker))
        return asset_obj.scalars().first()

    async def create(self, asset: Asset):
        try:
            self.db.add(asset)
            await self.db.commit()
            await self.db.refresh(asset)
            return asset 
        except IntegrityError:
            await self.db.rollback()
            raise ValueError(f"Такой тикер уже существует")
        
    async def delete(self, ticker: str) -> Optional[Asset]:
        result = await self.db.execute(select(Asset).filter(Asset.ticker == ticker))
        db_ticker = result.scalars().first()
        if db_ticker:
            await self.db.delete(db_ticker)
            await self.db.commit()
        return db_ticker
