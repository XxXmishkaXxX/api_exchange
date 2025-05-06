from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, delete
from typing import Optional
from fastapi import HTTPException


from app.core.logger import logger
from app.models.asset import Asset 
from app.db.database import redis_pool


class AssetRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    async def get_asset_by_ticker(self, ticker: str) -> int:
        asset_key = f"asset:{ticker}"

        logger.info(asset_key)
        async with redis_pool.connection() as redis:
            asset = await redis.hgetall(asset_key)
            
            logger.info(asset)
            
            if not asset:
                asset_obj = await self.session.execute(
                    select(Asset).where(Asset.ticker == ticker)
                )
                asset_obj = asset_obj.scalars().first()

                if asset_obj is None:
                    raise HTTPException(status_code=404, detail=f"Актив с тикером {ticker} не найден")
                
                await redis.hset(asset_key, mapping={"asset_id": asset_obj.id, "name": asset_obj.name})
                asset_id = asset_obj.id
            else:
                asset_id = int(asset["asset_id"])

        return asset_id

    async def create(self, asset: Asset):
        self.session.add(asset)
        return asset 
        
    async def delete(self, ticker: str) -> Optional[Asset]:
        result = await self.session.execute(select(Asset).filter(Asset.ticker == ticker))
        db_ticker = result.scalars().first()
        if db_ticker:
            await self.session.delete(db_ticker)
        return db_ticker
