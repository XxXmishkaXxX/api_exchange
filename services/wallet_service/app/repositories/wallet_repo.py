import json
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.models.wallet import Wallet
from app.models.wallet_asset import WalletAssetBalance
from app.models.asset import Asset
from app.db.database import redis_pool


class WalletRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _update_redis_wallet_data(self, user_id: UUID, asset_id: int, amount: int, locked: int, status: str = "ACTIVE"):
        stmt = select(Asset.ticker).where(Asset.id == asset_id)
        result = await self.session.execute(stmt)
        ticker = result.scalar_one_or_none()

        if ticker:
            key = f"wallet:user:{user_id}"
            async with redis_pool.connection() as redis:
                existing = await redis.get(key)
                wallet_data = json.loads(existing) if existing else {"status": status, "assets": {}}

                wallet_data["assets"][ticker] = {"amount": amount, "locked": locked}
                await redis.set(key, json.dumps(wallet_data))

    async def _get_wallet(self, user_id: UUID, origin: str) -> Wallet:
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        result = await self.session.execute(stmt)
        wallet = result.scalars().first()

        if not wallet or (wallet.status == "DEACTIVATE" and origin == "api"):
            raise ValueError(f"Кошелек пользователя {user_id} не найден или деактивирован")

        return wallet

    async def _get_asset(self, wallet_id: int, asset_id: int) -> WalletAssetBalance | None:
        stmt = select(WalletAssetBalance).options(selectinload(WalletAssetBalance.asset)).where(
            WalletAssetBalance.wallet_id == wallet_id,
            WalletAssetBalance.asset_id == asset_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, user_id: UUID):
        key = f"wallet:user:{user_id}"
        async with redis_pool.connection() as redis:
            data = await redis.get(key)
            if data:
                wallet_data = json.loads(data)
                if wallet_data.get("status") == "DEACTIVATE":
                    raise HTTPException(status_code=400, detail="Кошелек деактивирован")
                return {ticker: asset["amount"] for ticker, asset in wallet_data.get("assets", {}).items()}

        wallet = await self._get_wallet(user_id=user_id)

        if not wallet or wallet.status == "DEACTIVATE":
            raise HTTPException(status_code=400, detail="Кошелек не найден или деактивирован")

        stmt_balances = (
            select(WalletAssetBalance)
            .options(selectinload(WalletAssetBalance.asset))
            .where(WalletAssetBalance.wallet_id == wallet.id)
        )
        result_balances = await self.session.execute(stmt_balances)
        balances = result_balances.scalars().all()

        full_data = {
            "status": wallet.status,
            "assets": {
                balance.asset.ticker: {
                    "amount": balance.amount,
                    "locked": balance.locked
                }
                for balance in balances if balance.asset  
            }
        }

        async with redis_pool.connection() as redis:
            await redis.set(key, json.dumps(full_data))

        return {ticker: values["amount"] for ticker, values in full_data["assets"].items()}
    
    async def deactivate_user_wallet(self, user_id: UUID):
        wallet = await self._get_wallet(user_id, origin="exchange")
        wallet.status = "DEACTIVATE"
        
        key = f"wallet:user:{user_id}"
        async with redis_pool.connection() as redis:
            data = await redis.get(key)
            wallet_data = json.loads(data) if data else {"status": "ACTIVE", "assets": {}}
            wallet_data["status"] = "DEACTIVATE"
            await redis.set(key, json.dumps(wallet_data))

    async def get(self, user_id: UUID, asset_id: int, origin: str = "api") -> tuple[Wallet, WalletAssetBalance | None]:
        wallet = await self._get_wallet(user_id, origin=origin)
        asset = await self._get_asset(wallet.id, asset_id)
        return wallet, asset

    async def create(self, user_id: UUID):
        wallet = Wallet(user_id=user_id)
        self.session.add(wallet)

    async def deposit(self, user_id: UUID, asset_id: int, amount: int = 0):
        wallet, asset = await self.get(user_id, asset_id)
        if asset:
            asset.amount += amount
        else:
            asset = WalletAssetBalance(wallet_id=wallet.id, asset_id=asset_id, amount=amount, locked=0)
            self.session.add(asset)

        await self._update_redis_wallet_data(user_id, asset_id, asset.amount, asset.locked)

    async def withdraw(self, user_id: UUID, asset_id: int, amount: int = 0):
        _, asset = await self.get(user_id, asset_id)
        if not asset:
            raise ValueError(f"Актив {asset_id} не найден у пользователя {user_id}")
        if asset.amount - asset.locked < amount:
            raise HTTPException(status_code=400, detail="Недостаточно средств для вывода")

        asset.amount -= amount
        await self._update_redis_wallet_data(user_id, asset_id, asset.amount, asset.locked)

    async def lock(self, user_id: UUID, asset_id: int, lock: int = 0, origin="exchange"):
        _, asset = await self.get(user_id, asset_id, origin=origin)
        if not asset:
            raise ValueError(f"Asset {asset_id} not found for user {user_id}")
        if asset.amount - asset.locked < lock:
            raise ValueError("Недостаточно свободных средств для блокировки")

        asset.locked += lock
        await self._update_redis_wallet_data(user_id, asset_id, asset.amount, asset.locked)

    async def unlock(self, user_id: UUID, asset_id: int, unlock: int = 0):
        _, asset = await self.get(user_id, asset_id, origin="exchange")
        if not asset:
            raise ValueError(f"Asset {asset_id} not found for user {user_id}")

        asset.locked -= unlock
        await self._update_redis_wallet_data(user_id, asset_id, asset.amount, asset.locked)