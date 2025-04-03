from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, delete

from app.models.wallet import UserAssetBalance

class WalletRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, user_id: int):
        stmt = select(UserAssetBalance).where(UserAssetBalance.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get(self, user_id: int, ticker: str):
        stmt = select(UserAssetBalance).where(
            UserAssetBalance.user_id == user_id,
            UserAssetBalance.ticker == ticker
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, user_id: int, ticker: str, amount: int = 0):
        asset = UserAssetBalance(user_id=user_id, ticker=ticker, amount=amount, locked=0)
        self.session.add(asset)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ValueError("Запись с таким user_id и ticker уже существует")

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