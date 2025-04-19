from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException

from app.schemas.asset import AssetSchema
from app.repositories.asset_repo import AssetRepository
from app.services.producer import KafkaProducerService
from app.models.asset import Asset
from app.db.database import get_db

class AssetsService:

    def __init__(self, asset_repo: AssetRepository) -> None:
        self.repo = asset_repo

    async def get_list_assets(self):
        assets = await self.repo.get_all()
        return [{"ticker": asset.ticker, "name": asset.name} for asset in assets]

    async def get_assets_ids_pair(self, ticker1: str, ticker2: str):
        asset1_id = await self.repo.get_asset_by_ticker(ticker1)
        asset2_id = await self.repo.get_asset_by_ticker(ticker2)

        if not asset1_id or not asset2_id:
            raise HTTPException(status_code=404, detail="One or both tickers not found")

        return asset1_id.id, asset2_id.id

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
        

def get_assets_service(
    session: AsyncSession = Depends(get_db)
    ):
    return AssetsService(asset_repo=AssetRepository(session))