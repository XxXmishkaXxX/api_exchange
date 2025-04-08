from fastapi import Depends
from app.db.database import get_db
from app.services.producers import (get_change_balance_producer_service, 
                                    ChangeBalanceKafkaProducerService, 
                                    change_balance_producer_service)
from app.repositories.wallet_repo import WalletRepository
from app.repositories.asset_repo import AssetRepository
from app.services.wallet import WalletService

from contextlib import asynccontextmanager
from typing import AsyncGenerator


@asynccontextmanager
async def get_change_balance_producer_service() -> AsyncGenerator[ChangeBalanceKafkaProducerService, None]:
    yield change_balance_producer_service


async def get_change_balance_producer_service_direct():
    async with get_change_balance_producer_service() as producer:
        return producer


async def build_wallet_service(session) -> WalletService:
    wallet_repo = WalletRepository(session)
    asset_repo = AssetRepository(session)
    producer = await get_change_balance_producer_service_direct()

    return WalletService(wallet_repo, asset_repo, producer)


async def get_wallet_service(session=Depends(get_db)) -> WalletService:
    return await build_wallet_service(session)
