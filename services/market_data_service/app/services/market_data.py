from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.schemas.asset import AssetSchema
from app.repositories.asset_repo import AssetRepository
from app.services.producer import KafkaProducerService
from app.models.asset import Asset
from app.db.database import get_db

class MarketDataService:

    def __init__(self, asset_repo: AssetRepository) -> None:
        self.repo = asset_repo

    async def get_list_assets(self):
        assets = await self.repo.get_all()
        return [{"ticker": asset.ticker, "name": asset.name} for asset in assets]


    async def create_asset(self, asset: AssetSchema, producer: KafkaProducerService) -> dict:

        try:
            asset_data = asset.model_dump()
            asset = await self.repo.create(Asset(**asset_data) )
            
            data = {
                "action": "ADD",
                "asset_id": asset.id,
                "name": asset.name,
                "ticker": asset.ticker
            }
            await producer.send_message(data)

            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
        
    async def remove_asset(self, asset_ticker: str, producer: KafkaProducerService) -> dict:

        try:
            asset = await self.repo.delete(asset_ticker)

            data = {
                "action": "REMOVE",
                "ticker": asset.ticker
            }
            await producer.send_message(data)

            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
        

def get_market_data_service(
    session: AsyncSession = Depends(get_db)
    ):
    return MarketDataService(asset_repo=AssetRepository(session))