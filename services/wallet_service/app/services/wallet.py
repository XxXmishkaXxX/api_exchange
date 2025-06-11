from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from uuid import UUID

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

    async def get_all_assets_balance(self, user_id: UUID):
    	try:
        	assets = await self.wallet_repo.get_all(user_id)
        	return assets
    	except Exception as e:
        	raise HTTPException(status_code=404, detail=f"{e}")


    async def deposit_assets_user(self, data: DepositAssetsSchema) -> dict:
        """Пополнение баланса пользователя активом."""
        try:
            asset_id = await self.asset_repo.get_asset_by_ticker(ticker=data.ticker)
            if not asset_id:
                raise HTTPException(status_code=404, detail=f"Актив {data.ticker} не найден")
            
            await self.wallet_repo.deposit(user_id=data.user_id, asset_id=asset_id, amount=data.amount)
            return {"success": True}
        except HTTPException as e:
            raise e
        except ValueError as e:
            raise HTTPException(status_code=404, detail=f"{e}")
        except SQLAlchemyError as e:
            logger.error(f"Database error during deposit for user {data.user_id} and ticker {data.ticker}: {e}")
            raise HTTPException(status_code=500, detail="Ошибка при пополнении баланса")
        except Exception as e:
            logger.error(f"Unexpected error during deposit for user {data.user_id} and ticker {data.ticker}: {e}")
            raise HTTPException(status_code=500, detail="Неизвестная ошибка при пополнении")

    async def withdraw_assets_user(self, data: WithdrawAssetsSchema) -> dict:
        """Снятие активов с баланса пользователя."""

        asset_id = await self.asset_repo.get_asset_by_ticker(ticker=data.ticker)
        if not asset_id:
            raise HTTPException(status_code=404, detail=f"Актив {data.ticker} не найден")
        try:
            await self.wallet_repo.withdraw(data.user_id, asset_id, data.amount)
            return {"success": True}
        
        except HTTPException as e:
            raise e
        except ValueError as e:
            raise HTTPException(status_code=404, detail=f"{e}")
        except SQLAlchemyError as e:
            logger.error(f"Database error during withdrawal for user {data.user_id} and ticker {data.ticker}: {e}")
            raise HTTPException(status_code=500, detail="Ошибка при снятии активов")
        except Exception as e:
            logger.error(f"Unexpected error during withdrawal for user {data.user_id} and ticker {data.ticker}: {e}")
            raise HTTPException(status_code=500, detail="Неизвестная ошибка при снятии")
