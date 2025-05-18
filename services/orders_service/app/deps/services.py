from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_for_deps
from app.services.order import OrderService
from app.repositories.asset_repo import AssetRepository
from app.repositories.order_repo import OrderRepository

from app.kafka.producers.lock_assets_producer import (
    LockAssetsKafkaProducerService,
    get_lock_assets_producer,
    lock_assets_producer
)
from app.kafka.producers.market_quote_producer import (
    MarketQuoteKafkaProducerService,
    get_market_qoute_producer,
    market_quote_producer
)
from app.kafka.producers.order_producer import (
    OrderKafkaProducerService,
    get_order_producer,
    order_producer
)



async def get_order_service_in_deps(
    session: AsyncSession = Depends(get_db_for_deps),
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


def get_order_service(
    session: AsyncSession,
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