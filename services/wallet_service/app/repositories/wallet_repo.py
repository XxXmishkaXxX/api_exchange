from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, delete


from app.models.wallet import UserAssetBalance
from app.models.asset import Asset
from app.db.database import redis_pool
from app.repositories.asset_repo import AssetRepository


class WalletRepository:
    def __init__(self, session: AsyncSession, asset_repo: AssetRepository):
        self.asset_repo = asset_repo
        self.session = session

    async def get_all(self, user_id: int):
        stmt = (
            select(UserAssetBalance.amount, Asset.ticker)
            .join(Asset, UserAssetBalance.asset_id == Asset.id)
            .where(UserAssetBalance.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return {row.ticker: row.amount for row in result.all()}

    async def get(self, user_id: int, ticker: str) -> UserAssetBalance | None:
        
        async with redis_pool.connection() as redis:
            asset_key = f"asset:{ticker}"
            asset_id = await redis.hget(asset_key, "asset_id")

        if asset_id is None:
            # fallback
            stmt = select(Asset).where(Asset.ticker == ticker)
            result = await self.session.execute(stmt)
            asset = result.scalar_one_or_none()
            if asset is None:
                return None
            asset_id = asset.id

            async with redis_pool.connection() as redis:
                await redis.hset(asset_key, mapping={"asset_id": asset_id, "name": asset.name})

        stmt = select(UserAssetBalance).where(
            UserAssetBalance.user_id == user_id,
            UserAssetBalance.asset_id == int(asset_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, user_id: int, ticker: str, amount: int = 0):
        
        async with redis_pool.connection() as redis:
        
            redis_data = await redis.hgetall(f"asset:{ticker}")

            if redis_data:
                asset_id = int(redis_data["asset_id"])
            else:
                    # fallback в БД
                asset_obj = await self.asset_repo.get_asset_by_ticker(ticker)
                if not asset_obj:
                    raise ValueError(f"Актив {ticker} не найден")

                asset_id = asset_obj.id
                await redis.hset(
                    f"asset:{asset_obj.ticker}",
                    mapping={"asset_id": asset_obj.id, "name": asset_obj.name}
                )

        asset = UserAssetBalance(user_id=user_id, asset_id=asset_id, amount=amount, locked=0)
        self.session.add(asset)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ValueError("Запись с таким user_id и тикером уже существует")

    async def deposit(self, asset: UserAssetBalance, amount: int = 0):
        asset.amount += amount
        await self.session.commit()

    async def withdraw(self, asset: UserAssetBalance, amount: int = 0):
        if asset.amount < amount:
            raise ValueError("Недостаточно средств")
        asset.amount -= amount
        await self.session.commit()

    async def lock(self, asset: UserAssetBalance, lock: float = 0):
        if asset.amount < lock:
            raise ValueError("Недостаточно свободных средств для блокировки")
        asset.amount -= lock
        asset.locked += lock
        await self.session.commit()

    async def delete_all_assets_user(self, user_id: int):
        stmt = delete(UserAssetBalance).where(UserAssetBalance.user_id == user_id)
        await self.session.execute(stmt)
        await self.session.commit()