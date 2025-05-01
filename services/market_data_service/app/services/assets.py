from fastapi import HTTPException

from app.schemas.asset import AssetSchema
from app.repositories.asset_repo import AssetRepository
from app.kafka.producers.assets_producer import AssetsKafkaProducerService
from app.models.asset import Asset

class AssetsService:

    def __init__(self, asset_repo: AssetRepository, 
                 prod: AssetsKafkaProducerService) -> None:
        self.repo = asset_repo
        self.prod = prod

    async def get_list_assets(self):
        assets = await self.repo.get_all()
        return [{"ticker": asset.ticker, "name": asset.name} for asset in assets]

    async def get_assets_ids_pair(self, ticker1: str, ticker2: str):
        asset1_id = await self.repo.get_asset_by_ticker(ticker1)
        asset2_id = await self.repo.get_asset_by_ticker(ticker2)

        if not asset1_id or not asset2_id:
            raise HTTPException(status_code=404, detail="One or both tickers not found")

        return asset1_id.id, asset2_id.id

    async def create_asset(self, asset: AssetSchema) -> dict:

        try:
            asset_data = asset.model_dump()
            asset = await self.repo.create(Asset(**asset_data) )
            
            data = {
                "action": "ADD",
                "asset_id": asset.id,
                "name": asset.name,
                "ticker": asset.ticker
            }
            await self.prod.send_asset(data)

            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
        
    async def remove_asset(self, asset_ticker: str) -> dict:

        try:
            asset = await self.repo.delete(asset_ticker)

            data = {
                "action": "REMOVE",
                "ticker": asset.ticker
            }
            await self.prod.send_asset(data)

            return {"success": True}
        except Exception as e:
            return {"error": str(e)}