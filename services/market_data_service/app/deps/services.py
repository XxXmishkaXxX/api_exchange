from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.services.market_data import MarketDataService
from app.services.assets import AssetsService
from app.repositories.asset_repo import AssetRepository
from app.db.database import get_db_for_deps, redis_pool
from app.repositories.market_data import MarketDataRepository
from app.kafka.producers.assets_producer import get_assets_producer, AssetsKafkaProducerService




def get_market_data_service(session: AsyncSession = Depends(get_db_for_deps)):
    repo = MarketDataRepository(session=session, redis_session=redis_pool)
    return MarketDataService(repo)


def get_assets_service(
    session: AsyncSession = Depends(get_db_for_deps),
    producer: AssetsKafkaProducerService = Depends(get_assets_producer) 
    ):

    return AssetsService(asset_repo=AssetRepository(session),
                         prod=producer)