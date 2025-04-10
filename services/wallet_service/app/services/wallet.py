from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from app.repositories.wallet_repo import WalletRepository
from app.repositories.asset_repo import AssetRepository
from app.schemas.wallet import WithdrawAssetsSchema, DepositAssetsSchema
from app.core.logger import logger


class WalletService:
    def __init__(
        self,
        wallet_repo: WalletRepository,
        asset_repo: AssetRepository,
    ):
        self.wallet_repo = wallet_repo
        self.asset_repo = asset_repo

    async def get_all_assets_balance(self, user_id: int):
        return await self.wallet_repo.get_all(user_id)

    async def get_user_asset_balance(self, user_id: int, ticker: str) -> dict:
        """Получить баланс конкретного актива для пользователя."""
        try:
            user_asset, _ = await self._get_asset(user_id, ticker)
            if not user_asset:
                raise HTTPException(status_code=404, detail=f"Актива {ticker} у пользователя {user_id} не найдено")
            return {
                "amount": user_asset.amount,
                "locked": user_asset.locked
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching balance for user {user_id} and ticker {ticker}: {e}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка базы данных")

    async def get_user_asset_balance_from_cache(self, user_id: int, ticker: str) -> dict:
        """Получить баланс актива из Redis, с фолбэком на БД."""
        try:
            balance = await self.wallet_repo.get_hash(user_id, ticker)
            if balance:
                return balance

            asset_id = await self.asset_repo.get_asset_by_ticker(ticker)
            if asset_id is None:
                raise HTTPException(status_code=404, detail=f"Ассет {ticker} не найден")

            user_asset = await self.wallet_repo.get(user_id, asset_id)
            if not user_asset:
                raise HTTPException(status_code=404, detail=f"Баланс по {ticker} у пользователя {user_id} не найден")

            return {
                "amount": user_asset.amount,
                "locked": user_asset.locked
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching balance from cache for user {user_id} and ticker {ticker}: {e}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка базы данных")

    async def deposit_assets_user(self, data: DepositAssetsSchema) -> dict:
        """Пополнение баланса пользователя активом."""
        try:
            user_asset, asset_id = await self._get_asset(user_id=data.user_id, ticker=data.ticker)

            if not user_asset:
                await self.wallet_repo.create(data.user_id, asset_id, data.amount)
                user_asset = await self.wallet_repo.get(data.user_id, asset_id)
            else:
                await self.wallet_repo.deposit(user_asset, data.amount)

            return {"success": True}
        except SQLAlchemyError as e:
            logger.error(f"Database error during deposit for user {data.user_id} and ticker {data.ticker}: {e}")
            raise HTTPException(status_code=500, detail="Ошибка при пополнении баланса")
        except Exception as e:
            logger.error(f"Unexpected error during deposit for user {data.user_id} and ticker {data.ticker}: {e}")
            raise HTTPException(status_code=500, detail="Неизвестная ошибка при пополнении")

    async def withdraw_assets_user(self, data: WithdrawAssetsSchema) -> dict:
        """Снятие активов с баланса пользователя."""

        user_asset, _ = await self._get_asset(user_id=data.user_id, ticker=data.ticker)

        if not user_asset:
            raise HTTPException(status_code=404, detail=f"Актива {data.ticker} у пользователя {data.user_id} не найдено")

        try:
            await self.wallet_repo.withdraw(user_asset, data.amount)
            return {"success": True}
        except SQLAlchemyError as e:
            logger.error(f"Database error during withdrawal for user {data.user_id} and ticker {data.ticker}: {e}")
            raise HTTPException(status_code=500, detail="Ошибка при снятии активов")
        except Exception as e:
            logger.error(f"Unexpected error during withdrawal for user {data.user_id} and ticker {data.ticker}: {e}")
            raise HTTPException(status_code=500, detail="Неизвестная ошибка при снятии")

    async def _get_asset(self, user_id: int, ticker: str):
        try:
            asset_id = await self.asset_repo.get_asset_by_ticker(ticker)
            if asset_id is None:
                raise HTTPException(status_code=404, detail=f"Ассет {ticker} не найден")
            user_asset = await self.wallet_repo.get(user_id, asset_id)
            return user_asset, asset_id
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching asset for user {user_id} and ticker {ticker}: {e}")
            raise HTTPException(status_code=500, detail="Ошибка при получении актива")
        except Exception as e:
            logger.error(f"Unexpected error while fetching asset for user {user_id} and ticker {ticker}: {e}")
            raise HTTPException(status_code=500, detail="Неизвестная ошибка при получении актива")