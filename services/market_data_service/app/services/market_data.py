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

<<<<<<< Updated upstream
    async def get_list_assets(self):
        assets = await self.repo.get_all()
        return [{"ticker": asset.ticker, "name": asset.name} for asset in assets]
=======
    async def get_orderbook(self, data: OrderBookRequest):
        ticker_pair = data.ticker_pair
        orderbook_data = await self.repo.get_orderbook(ticker_pair)

        if orderbook_data is None:
            return OrderBookErrorResponse(detail=f"Orderbook not found for {data.full_symbol}")

        if data.limit:
            orderbook_data['bids'] = orderbook_data['bids'][:data.limit]
            orderbook_data['asks'] = orderbook_data['asks'][:data.limit]

        return OrderBookResponse(
            bids=[Order(price=int(order["price"]), amount=int(order["qty"])) for order in orderbook_data["bids"]],
            asks=[Order(price=int(order["price"]), amount=int(order["qty"])) for order in orderbook_data["asks"]],
        )

    async def get_transactions(self, asset1_id: int, asset2_id: int, limit: int, offset: int):
        transactions = await self.repo.get_all_transaction_by_pair(asset1_id, asset2_id, limit, offset)
        return self._format_transactions(transactions, "Transactions not found for the given asset pair.")

    async def get_user_transactions_by_pair(self, asset1_id: int, asset2_id: int, user_id: int, limit: int, offset: int):
        transactions = await self.repo.get_all_user_transactions_by_pair(
            asset1_id=asset1_id, asset2_id=asset2_id, user_id=user_id, limit=limit, offset=offset
        )
        return self._format_transactions(transactions, "Transactions not found for the given asset pair and user id.")

    async def get_all_user_transactions(self, user_id: int, limit: int, offset: int):
        transactions = await self.repo.get_all_user_transactions(user_id, limit, offset)
        return self._format_transactions(transactions, "Transactions not found for the given user id.")

    def _format_transactions(self, transactions, error_msg: str) -> List[Transaction]:
        if not transactions:
            raise HTTPException(status_code=404, detail=error_msg)

        return [
            Transaction(
                ticker=transaction.order_asset.ticker,
                amount=transaction.amount,
                price=transaction.price,
                timestamp=transaction.created_at.isoformat(),
            )
            for transaction in transactions
        ]
>>>>>>> Stashed changes


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