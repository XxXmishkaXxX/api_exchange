from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_for_deps

from app.repositories.wallet_repo import WalletRepository
from app.repositories.asset_repo import AssetRepository
from app.services.wallet import WalletService



async def get_wallet_service(session: AsyncSession = Depends(get_db_for_deps)) -> WalletService:
    wallet_repo = WalletRepository(session)
    asset_repo = AssetRepository(session)

    return WalletService(wallet_repo, asset_repo)