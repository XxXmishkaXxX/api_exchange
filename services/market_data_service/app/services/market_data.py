from fastapi import HTTPException
from typing import List
from uuid import UUID
from datetime import timezone


from app.repositories.market_data import MarketDataRepository
from app.schemas.orderbook import OrderBookRequest, OrderBookResponse, OrderBookErrorResponse, Order
from app.schemas.transactions import Transaction


class MarketDataService:

    def __init__(self, repo: MarketDataRepository):
        self.repo = repo
        
    async def get_list_assets(self):
        assets = await self.repo.get_all()
        return [{"ticker": asset.ticker, "name": asset.name} for asset in assets]

    async def get_orderbook(self, data: OrderBookRequest):
        ticker_pair = data.ticker_pair
        orderbook_data = await self.repo.get_orderbook(ticker_pair)

        if orderbook_data is None:
            return OrderBookErrorResponse(detail=f"Orderbook not found for {data.full_symbol}")

        if data.limit:
            orderbook_data['bids'] = orderbook_data['bids'][:data.limit]
            orderbook_data['asks'] = orderbook_data['asks'][:data.limit]

        return OrderBookResponse(
            bid_levels=[Order(price=int(order["price"]), qty=int(order["qty"])) for order in orderbook_data["bids"]],
            ask_levels=[Order(price=int(order["price"]), qty=int(order["qty"])) for order in orderbook_data["asks"]],
        )

    async def get_transactions(self, asset1_id: int, asset2_id: int, limit: int, offset: int):
        transactions = await self.repo.get_all_transaction_by_pair(asset1_id, asset2_id, limit, offset)
        return self._format_transactions(transactions, "Transactions not found for the given asset pair.")

    async def get_user_transactions_by_pair(self, asset1_id: int, asset2_id: int, user_id: UUID, limit: int, offset: int):
        transactions = await self.repo.get_all_user_transactions_by_pair(
            asset1_id=asset1_id, asset2_id=asset2_id, user_id=user_id, limit=limit, offset=offset
        )
        return self._format_transactions(transactions, "Transactions not found for the given asset pair and user id.")

    async def get_all_user_transactions(self, user_id: UUID, limit: int, offset: int):
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
                timestamp=transaction.created_at.replace(tzinfo=timezone.utc),
            )
            for transaction in transactions
        ]
