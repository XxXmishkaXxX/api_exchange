from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.order import OrderService
from app.repositories.asset_repo import AssetRepository
from app.repositories.order_repo import OrderRepository

from app.services.producers import (
    OrderKafkaProducerService,
    LockAssetsKafkaProducerService,
    MarketQuoteKafkaProducerService,
    get_order_producer,
    get_lock_assets_producer,
    get_market_qoute_producer,
)

async def get_order_service(
    session: AsyncSession = Depends(get_db),
    order_producer: OrderKafkaProducerService = Depends(get_order_producer),
    lock_assets_producer: LockAssetsKafkaProducerService = Depends(get_lock_assets_producer),
    market_quote_producer: MarketQuoteKafkaProducerService = Depends(get_market_qoute_producer),
) -> OrderService:
    order_repo = OrderRepository(session)
    asset_repo = AssetRepository(session)
    return OrderService(
        order_repo=order_repo,
        asset_repo=asset_repo,
        order_producer=order_producer,
        lock_assets_producer=lock_assets_producer,
        market_quote_producer=market_quote_producer,
    )
