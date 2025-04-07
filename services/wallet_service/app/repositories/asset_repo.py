from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, delete
from typing import Optional

from app.models.asset import Asset 
from app.db.database import redis_pool


class AssetRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    async def get_asset_by_ticker(self, ticker: str) -> Asset:

        asset_key = f"asset:{ticker}"

        async with redis_pool.connection() as redis:
            asset = await redis.hgetall(asset_key)
            
            if not asset:
                result = await self.session.execute(
                select(Asset).where(Asset.ticker == ticker))

                asset_obj = result.scalars().first()
                
                if asset_obj is None:
                    raise ValueError(f"Asset with ticker {ticker} not found.")
                
                await redis.hset(asset_key, mapping={"asset_id":asset_obj.id,"name": asset_obj.name})
                asset_id = asset_obj.id
            else:
                asset_id = int(asset.get("asset_id", 0))

        return asset_id

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
