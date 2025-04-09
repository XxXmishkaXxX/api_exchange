from fastapi import Depends
from app.db.database import get_db

from app.repositories.wallet_repo import WalletRepository
from app.repositories.asset_repo import AssetRepository
from app.services.wallet import WalletService




async def build_wallet_service(session) -> WalletService:
    wallet_repo = WalletRepository(session)
    asset_repo = AssetRepository(session)

    return WalletService(wallet_repo, asset_repo)


async def get_wallet_service(session=Depends(get_db)) -> WalletService:
    return await build_wallet_service(session)
