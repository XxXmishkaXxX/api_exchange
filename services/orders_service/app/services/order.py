import asyncio
import uuid
from uuid import UUID
from fastapi import HTTPException


from app.repositories.order_repo import OrderRepository
from app.repositories.asset_repo import AssetRepository
from app.schemas.order import (
    OrderSchema,
    OrderCancelResponse,
    OrderCreateResponse,
    OrderResponse,
    OrderListResponse,
    StatusOrder,
)
from app.models.order import Order
from app.services.response_listeners import lock_futures, market_quote_futures
from app.services.producers import (
    OrderKafkaProducerService,
    LockAssetsKafkaProducerService,
    MarketQuoteKafkaProducerService,
)
from app.core.logger import logger


class OrderService:
    def __init__(self, order_repo: OrderRepository, asset_repo: AssetRepository):
        self.order_repo = order_repo
        self.asset_repo = asset_repo

    async def get_order(self, user_data: dict, order_id: UUID) -> OrderResponse:
        user_id = UUID(user_data["sub"])
        order = await self.order_repo.get(order_id, user_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return self._build_order_response(order)

    async def get_list_order(self, user_data: dict) -> OrderListResponse:
        user_id = UUID(user_data["sub"])
        orders = await self.order_repo.get_list(user_id)
        return OrderListResponse(orders=[self._build_order_response(o) for o in orders])

    async def create_order(
        self,
        user_data: dict,
        order: OrderSchema,
        prod_order: OrderKafkaProducerService,
        prod_lock: LockAssetsKafkaProducerService,
        prod_get_market_quote: MarketQuoteKafkaProducerService,
    ) -> OrderCreateResponse:
        user_id = UUID(user_data["sub"])
        order_asset_id = await self.asset_repo.get_asset_by_ticker(order.ticker)
        payment_asset_id = await self.asset_repo.get_asset_by_ticker(order.payment_ticker)

        if not order_asset_id or not payment_asset_id:
            missing = []
            if not order_asset_id:
                missing.append(f"order asset '{order.ticker}'")
            if not payment_asset_id:
                missing.append(f"payment asset '{order.payment_ticker}'")
            raise HTTPException(status_code=404, detail=f"Asset(s) not found: {', '.join(missing)}")

        if order.type == "market":
            price = await self._get_market_quote(order, prod_get_market_quote)
            ticker, asset_id, amount = self._prepare_lock_params(
                order, price, order_asset_id, payment_asset_id, is_total_price=True
            )
        else:
            ticker, asset_id, amount = self._prepare_lock_params(
                order, order.price, order_asset_id, payment_asset_id
            )

        await self._lock_assets(user_id, ticker, asset_id, amount, prod_lock)

        order_entity = Order(
            user_id=user_id,
            type=order.type,
            status=StatusOrder.NEW,
            direction=order.direction,
            qty=order.qty,
            price=order.price,
            order_asset_id=order_asset_id,
            payment_asset_id=payment_asset_id,
        )
        order_entity = await self.order_repo.create(order_entity)

        try:
            await prod_order.send_order(order.ticker, order.payment_ticker, order=order_entity)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка отправки ордера в Matching Engine: {e}")

        return OrderCreateResponse(success=True, order_id=order_entity.id)

    async def cancel_order(
        self,
        user_data: dict,
        order_id: UUID,
        prod_order: OrderKafkaProducerService,
    ) -> OrderCancelResponse:
        user_id = UUID(user_data["sub"])
        order = await self.order_repo.get(order_id, user_id)

        if not order:
            raise HTTPException(status_code=404, detail="Такого ордера не существует")

        await prod_order.cancel_order(
            order_id=order_id,
            direction=order.direction,
            order_ticker=order.order_asset.ticker,
            payment_ticker=order.payment_asset.ticker,
        )
        return OrderCancelResponse(success=True)

    async def _lock_assets(self, user_id, ticker, asset_id, amount, prod_lock):
        correlation_id = str(uuid.uuid4())
        try:
            await prod_lock.lock_assets(
                user_id=user_id,
                asset_id=asset_id,
                ticker=ticker,
                amount=amount,
                correlation_id=correlation_id,
            )
            success = await self._wait_for_lock_confirmation(correlation_id)
            if not success:
                raise HTTPException(status_code=400, detail=f"Недостаточно средств {ticker}")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Таймаут ожидания блокировки активов.")
        except Exception as e:
            logger.error(f"Ошибка локации активов: {e}")
            raise HTTPException(status_code=500, detail="Ошибка при попытке локации активов")

    async def _get_market_quote(self, order, prod_get_market_quote) -> int:
        correlation_id = str(uuid.uuid4())
        await prod_get_market_quote.send_request(
            correlation_id=correlation_id,
            order_ticker=order.ticker,
            payment_ticker=order.payment_ticker,
            amount=order.qty,
            direction=order.direction,
        )
        result = await self._wait_for_market_quote(correlation_id)
        if result.get("status") != "ok":
            raise HTTPException(status_code=400, detail=result.get("reason", "Не удалось получить цену"))
        if order.direction == "buy":
            return int(result["amount_to_pay"])
        return int(order.qty)

    def _prepare_lock_params(self, order, price, order_asset_id, payment_asset_id, is_total_price=False):
        is_buy = order.direction == "buy"
        ticker = order.payment_ticker if is_buy else order.ticker
        asset_id = payment_asset_id if is_buy else order_asset_id
        amount = int(price) if is_total_price and is_buy else (int(order.qty * price) if is_buy else order.qty)
        return ticker, asset_id, amount


    async def _wait_for_lock_confirmation(self, correlation_id: str, timeout: int = 5) -> bool:
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        lock_futures[correlation_id] = future
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            lock_futures.pop(correlation_id, None)
            return False

    async def _wait_for_market_quote(self, correlation_id: str, timeout: int = 5):
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        market_quote_futures[correlation_id] = future
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            market_quote_futures.pop(correlation_id, None)
            raise

    def _build_order_response(self, order: Order) -> OrderResponse:
        return OrderResponse(
            order_id=order.id,
            user_id=order.user_id,
            status=order.status,
            timestamp=order.updated_at.isoformat(),
            body=OrderSchema(
                type=order.type,
                direction=order.direction,
                ticker=order.order_asset.ticker,
                payment_order_ticker=order.payment_asset.ticker,
                qty=order.qty,
                price=order.price,
            ),
            filled=order.filled,
        )