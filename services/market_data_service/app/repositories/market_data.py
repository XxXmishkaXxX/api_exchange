import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


from app.models.transaction import Transaction



class MarketDataRepository:
    def __init__(self, session: AsyncSession, redis_session):
        self.session = session
        self.redis_session = redis_session

    async def add_transaction(self, transaction: Transaction):
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def get_all_transaction_by_pair(self, asset1_id: int, asset2_id: int, limit: int, offset: int):
            query = (
                select(Transaction)
                .where(Transaction.order_asset_id == asset1_id, Transaction.payment_asset_id == asset2_id)
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(query)
            return result.scalars().all()

    async def get_all_user_transactions_by_pair(self, user_id: int, asset1_id: int, asset2_id: int, limit: int, offset: int):
        stmt = select(Transaction).where(
            Transaction.from_user_id == user_id,
            Transaction.order_asset_id == asset1_id,
            Transaction.payment_asset_id == asset2_id
        ).limit(limit).offset(offset)

        transactions = await self.session.execute(stmt)
        transactions = transactions.scalars().all()

        return transactions
    
    async def get_all_user_transactions(self, user_id: int, limit: int, offset: int):
        stmt = select(Transaction).where(
            Transaction.from_user_id == user_id).limit(
                limit).offset(offset)

        transactions = await self.session.execute(stmt)
        transactions = transactions.scalars().all()
        
        return transactions

    
    async def get_orderbook(self, ticker_pair: str):
        
        async with self.redis_session.connection() as redis:
   
            key = f"market_snapshot:{ticker_pair}"
            data = await redis.hgetall(key)
        
            if data is None:
                return None
        
            return {
                "bids": json.loads(data.get("bid_levels", "[]")),
                "asks": json.loads(data.get("ask_levels", "[]")),
            }
