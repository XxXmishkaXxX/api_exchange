from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from uuid import UUID

from app.models.wallet import Wallet
from app.models.wallet_asset import WalletAssetBalance
from app.models.asset import Asset
from app.core.logger import logger
from app.db.database import redis_pool


class WalletRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _update_redis_balance(self, user_id: UUID, asset_id: int, amount: int, locked: int):
        stmt = select(Asset.ticker).where(Asset.id == asset_id)
        result = await self.session.execute(stmt)
        ticker = result.scalar_one_or_none()

        if ticker:
            redis_key = f"user:{str(user_id)}:asset:{ticker}"
            async with redis_pool.connection() as redis:
                await redis.hset(redis_key, mapping={"amount": amount, "locked": locked})

    async def get_all(self, user_id: UUID):
        redis_pattern = f"user:{str(user_id)}:asset:*"
        data = {}

        async with redis_pool.connection() as redis:
            cursor = b"0"
            while cursor != 0:
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
                stmt_balances = select(WalletAssetBalance.amount, WalletAssetBalance.asset_id, WalletAssetBalance.locked).join(Wallet).where(Wallet.user_id == user_id)
                result_balances = await self.session.execute(stmt_balances)
                balances = {row.asset_id: {"amount": row.amount, "locked": row.locked} for row in result_balances.all()}

                stmt_assets = select(Asset.ticker, Asset.id).where(Asset.id.in_(balances.keys()))
                result_assets = await self.session.execute(stmt_assets)
                asset_tickers = {row.id: row.ticker for row in result_assets.all()}

                for asset_id, balance in balances.items():
                    ticker = asset_tickers.get(asset_id)
                    if ticker:
                        data[ticker] = {"amount": balance["amount"]}
                        redis_key = f"user:{str(user_id)}:asset:{ticker}"
                        await redis.hset(redis_key, mapping={"amount": balance["amount"], "locked": balance["locked"]})

        return {ticker: values["amount"] for ticker, values in data.items()}

    async def get(self, user_id: UUID, asset_id: int) -> tuple[Wallet | None, WalletAssetBalance | None]:
        
        stmt = select(Wallet).where(
            Wallet.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        
        wallet = result.scalars().first()
        
        if not wallet:
            raise ValueError(f"Кошелек пользователя {user_id} не найден")
        
        stmt = select(WalletAssetBalance).where(
            WalletAssetBalance.wallet_id == wallet.id,
            WalletAssetBalance.asset_id == asset_id)
        
        result = await self.session.execute(stmt)
        asset = result.scalars().first()

        return wallet, asset

    async def create(self, user_id: UUID) -> None:
        wallet = Wallet(user_id=user_id)
        self.session.add(wallet)

    async def deposit(self, user_id: UUID, asset_id: int, amount: int = 0):
        wallet, asset = await self.get(user_id=user_id, asset_id=asset_id)
        
        if asset:
            asset.amount += amount
        else:
            asset = WalletAssetBalance(wallet_id=wallet.id, asset_id=asset_id, amount=amount,
                                       locked=0)
            self.session.add(asset)


        await self._update_redis_balance(user_id, asset_id, asset.amount, asset.locked)

    async def withdraw(self, user_id: UUID, asset_id: int, amount: int = 0):
        _, asset = await self.get(user_id=user_id, asset_id=asset_id)
        if asset is None:
            raise ValueError(f"Asset {asset_id} not found for user {user_id}")
        if asset.amount - asset.locked < amount:
            raise HTTPException(status_code=400, detail="Недостаточно средств для вывода")
        asset.amount -= amount

        await self._update_redis_balance(user_id, asset_id, asset.amount, asset.locked)

    async def lock(self, user_id: UUID, asset_id: int, lock: int = 0):
        _, asset = await self.get(user_id=user_id, asset_id=asset_id)
        if asset is None:
            raise ValueError(f"Asset {asset_id} not found for user {user_id}")
        if asset.amount - asset.locked < lock:
            raise ValueError("Недостаточно свободных средств для блокировки")
        asset.locked += lock

        await self._update_redis_balance(user_id, asset_id, asset.amount, asset.locked)

    async def unlock(self, user_id: UUID, asset_id: int, unlock: int = 0):
        _, asset = await self.get(user_id=user_id, asset_id=asset_id)
        if asset is None:
            raise ValueError(f"Asset {asset_id} not found for user {user_id}")
        asset.locked -= unlock

        await self._update_redis_balance(user_id, asset_id, asset.amount, asset.locked)

    async def delete_all_assets_user(self, user_id: UUID):
        stmt = delete(Wallet).where(Wallet.user_id == user_id)
        await self.session.execute(stmt)

        redis_pattern = f"user:{str(user_id)}:asset:*"
        async with redis_pool.connection() as redis:
            cursor = b"0"
            while cursor != 0:
                cursor, keys = await redis.scan(cursor=cursor, match=redis_pattern)
                if keys:
                    await redis.delete(*keys)
