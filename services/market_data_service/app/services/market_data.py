from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from typing import List
from app.db.database import get_db, redis_pool
from app.repositories.market_data import MarketDataRepository
from app.schemas.orderbook import OrderBookRequest, OrderBookResponse, OrderBookErrorResponse, Order
from app.schemas.transactions import Transaction


class MarketDataService:

    def __init__(self, repo: MarketDataRepository):
        self.repo = repo

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
                ticker=transaction.ticker,
                amount=transaction.amount,
                price=transaction.price,
                timestamp=transaction.created_at.isoformat(),
            )
            for transaction in transactions
        ]


def get_market_data_service(session: AsyncSession = Depends(get_db)):
    repo = MarketDataRepository(session=session, redis_session=redis_pool)
    return MarketDataService(repo)
