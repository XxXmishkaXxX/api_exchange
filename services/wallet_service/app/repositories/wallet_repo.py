import json
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, delete


from app.models.wallet import UserAssetBalance
from app.models.asset import Asset
from app.core.logger import logger
from app.db.database import redis_pool


import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, delete

from app.models.wallet import UserAssetBalance
from app.models.asset import Asset
from app.core.logger import logger
from app.db.database import redis_pool


class WalletRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _update_redis_balance(self, user_id: int, asset_id: int, amount: int, locked: int):
        stmt = select(Asset.ticker).where(Asset.id == asset_id)
        result = await self.session.execute(stmt)
        ticker = result.scalar_one_or_none()

        if ticker:
            redis_key = f"user:{user_id}:asset:{ticker}"
            async with redis_pool.connection() as redis:
                await redis.hset(redis_key, mapping={"amount": amount, "locked": locked})

    async def get_all(self, user_id: int):
        redis_pattern = f"user:{user_id}:asset:*"
        data = {}

        async with redis_pool.connection() as redis:
            cursor = b"0"
            while cursor != b"0":
                cursor, keys = await redis.scan(cursor=cursor, match=redis_pattern)
                for key in keys:
                    asset_data = await redis.hgetall(key)
                    if asset_data:
                        ticker = key.decode().split(":")[-1]
                        data[ticker] = {
                            "amount": int(asset_data.get(b"amount", b"0")),
                            "locked": int(asset_data.get(b"locked", b"0")),
                        }

            if not data:
                stmt_balances = select(UserAssetBalance.amount, UserAssetBalance.asset_id, UserAssetBalance.locked).where(UserAssetBalance.user_id == user_id)
                result_balances = await self.session.execute(stmt_balances)
                balances = {row.asset_id: {"amount": row.amount, "locked": row.locked} for row in result_balances.all()}

                stmt_assets = select(Asset.ticker, Asset.id).where(Asset.id.in_(balances.keys()))
                result_assets = await self.session.execute(stmt_assets)
                asset_tickers = {row.id: row.ticker for row in result_assets.all()}

                for asset_id, balance in balances.items():
                    ticker = asset_tickers.get(asset_id)
                    if ticker:
                        data[ticker] = {"amount": balance["amount"]}
                        redis_key = f"user:{user_id}:asset:{ticker}"
                        await redis.hset(redis_key, mapping={"amount": balance["amount"], "locked": balance["locked"]})

        return {ticker: values["amount"] for ticker, values in data.items()}

    async def get(self, user_id: int, asset_id: int) -> UserAssetBalance | None:
        stmt = select(UserAssetBalance).where(
            UserAssetBalance.user_id == user_id,
            UserAssetBalance.asset_id == asset_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    

    async def get_hash(self, user_id: int, ticker: str) -> dict[str, int] | None:
        redis_key = f"user:{user_id}:asset:{ticker}"
        async with redis_pool.connection() as redis:
            asset_data = await redis.hgetall(redis_key)
            if asset_data:
                return {
                    "amount": int(asset_data.get(b"amount", b"0")),
                    "locked": int(asset_data.get(b"locked", b"0")),
                }
        return None

    async def create(self, user_id: int, asset_id: int, amount: int = 0):
        asset = UserAssetBalance(user_id=user_id, asset_id=asset_id, amount=amount, locked=0)
        self.session.add(asset)
        try:
            await self.session.commit()
            await self._update_redis_balance(user_id, asset_id, amount, 0)
        except IntegrityError:
            await self.session.rollback()
            raise ValueError("Запись с таким user_id и тикером уже существует")

    async def deposit(self, asset: UserAssetBalance, amount: int = 0):
        asset.amount += amount
        await self.session.commit()
        await self._update_redis_balance(asset.user_id, asset.asset_id, asset.amount, asset.locked)


    async def withdraw(self, asset: UserAssetBalance, amount: int = 0):
        if asset.amount < amount:
            raise HTTPException(status_code=400, detail="Недостаточно средств для вывода")
        asset.amount -= amount
        await self.session.commit()
        await self._update_redis_balance(asset.user_id, asset.asset_id, asset.amount, asset.locked)


    async def lock(self, asset: UserAssetBalance, lock: int = 0):
        if asset.amount < lock:
            raise ValueError("Недостаточно свободных средств для блокировки")
        asset.locked += lock
        await self.session.commit()
        await self.session.refresh(asset)
        await self._update_redis_balance(asset.user_id, asset.asset_id, asset.amount, asset.locked)

    async def unlock(self, asset: UserAssetBalance, unlock: int = 0):
        asset.locked -= unlock
        await self.session.commit()
        await self.session.refresh(asset)
        await self._update_redis_balance(asset.user_id, asset.asset_id, asset.amount, asset.locked)

    async def delete_all_assets_user(self, user_id: int):
        stmt = delete(UserAssetBalance).where(UserAssetBalance.user_id == user_id)
        await self.session.execute(stmt)
        await self.session.commit()

        redis_pattern = f"user:{user_id}:asset:*"
        async with redis_pool.connection() as redis:
            cursor = b"0"
            while cursor != 0:
                cursor, keys = await redis.scan(cursor=cursor, match=redis_pattern)
                if keys:
                    await redis.delete(*keys)
