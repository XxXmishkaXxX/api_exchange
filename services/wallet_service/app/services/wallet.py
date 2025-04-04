from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.repositories.wallet_repo import WalletRepository
from app.repositories.asset_repo import AssetRepository
from app.db.database import get_db
from app.schemas.wallet import WithdrawAssetsSchema, DepositAssetsSchema
from app.services.producers import ChangeBalanceKafkaProducerService

class WalletService:
    def __init__(self, wallet_repo: WalletRepository):
        self.wallet_repo = wallet_repo

    async def get_all_assets_balance(self, user_id: int):
        return await self.wallet_repo.get_all(user_id)

    async def deposit_assets_user(self, data: DepositAssetsSchema, 
                                  prod: ChangeBalanceKafkaProducerService):
        asset = await self.wallet_repo.get(data.user_id, data.ticker)
        if not asset:
            await self.wallet_repo.create(data.user_id, data.ticker, data.amount)
        else:
            await self.wallet_repo.deposit(asset, data.amount)

        message = {
            "action": "deposit",
            "user_id": data.user_id,
            "asset": data.ticker,
            "amount": data.amount 
        }
        await prod.send_message(message)
        
        return {"success": True}

    async def withdraw_assets_user(self, data: WithdrawAssetsSchema,
                                   prod: ChangeBalanceKafkaProducerService):
        asset = await self.wallet_repo.get(data.user_id, data.ticker)
        if not asset:
            raise ValueError("Актив не найден")
        await self.wallet_repo.withdraw(asset, data.amount)

        message = {
            "action": "withdraw",
            "user_id": data.user_id,
            "asset": data.ticker,
            "amount": data.amount 
        }
        
        await prod.send_message(message)
        return {"success": True}


def get_wallet_service(
    session: AsyncSession = Depends(get_db)
) -> WalletService:
    """
    Функция для получения экземпляра wallet service.

    Аргументы:
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
        WalletService: Экземпляр wallet service.
    """
    asset_repo = AssetRepository(session)
    wallet_repo = WalletRepository(session, asset_repo)
    return WalletService(wallet_repo=wallet_repo)
