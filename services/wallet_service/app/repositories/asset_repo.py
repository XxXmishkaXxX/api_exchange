from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from app.models.asset import Asset
from app.db.database import redis_pool


class AssetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_asset_by_ticker(self, ticker: str) -> int:
        asset_key = f"asset:{ticker}"

        async with redis_pool.connection() as redis:
            asset_data = await redis.hgetall(asset_key)

            if asset_data:
                return int(asset_data.get("asset_id"))

            result = await self.session.execute(
                select(Asset).where(Asset.ticker == ticker)
            )
            asset_obj = result.scalars().first()

            if asset_obj is None:
                raise HTTPException(status_code=404, detail=f"Ассет {ticker} не найден")

            await redis.hset(asset_key, mapping={"asset_id": asset_obj.id, "name": asset_obj.name})
            return asset_obj.id

    async def create(self, asset: Asset) -> Asset:
        self.session.add(asset)
        return asset

    async def delete(self, ticker: str) -> Optional[Asset]:
        result = await self.session.execute(select(Asset).where(Asset.ticker == ticker))
        db_asset = result.scalars().first()

        if db_asset:
            await self.session.delete(db_asset)
        return db_asset
