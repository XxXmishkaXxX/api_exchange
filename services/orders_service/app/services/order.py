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
    MarketOrderSchema,
    LimitOrderSchema,
    LimitOrderResponse,
    MarketOrderResponse
)
from app.models.order import Order
from app.services.response_listeners import lock_futures, market_quote_futures
from app.kafka.producers.lock_assets_producer import LockAssetsKafkaProducerService
from app.kafka.producers.market_quote_producer import MarketQuoteKafkaProducerService
from app.kafka.producers.order_producer import OrderKafkaProducerService
from app.core.logger import logger


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        asset_repo: AssetRepository,
        order_producer: OrderKafkaProducerService,
        lock_assets_producer: LockAssetsKafkaProducerService,
        market_quote_producer: MarketQuoteKafkaProducerService,
    ):
        self.order_repo = order_repo
        self.asset_repo = asset_repo

        self.order_producer = order_producer
        self.lock_assets_producer = lock_assets_producer
        self.market_quote_producer = market_quote_producer

    async def get_order(self, user_id: UUID, order_id: UUID) -> OrderResponse:
        order = await self.order_repo.get(order_id, user_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return self._build_order_response(order)

    async def get_list_order(self, user_id: UUID) -> OrderListResponse:
        orders = await self.order_repo.get_list(user_id)
        return OrderListResponse([self._build_order_response(o) for o in orders])

    async def create_order(
        self,
        user_id: UUID,
        order: OrderSchema
    ) -> OrderCreateResponse:
        order_asset_id = await self.asset_repo.get_asset_by_ticker(order.ticker)
        payment_asset_id = await self.asset_repo.get_asset_by_ticker(order.payment_ticker)

        if not order_asset_id or not payment_asset_id:
            missing = []
            if not order_asset_id:
                missing.append(f"order asset '{order.ticker}'")
            if not payment_asset_id:
                missing.append(f"payment asset '{order.payment_ticker}'")
            raise HTTPException(status_code=404, detail=f"Asset(s) not found: {', '.join(missing)}")

        if order.price:
            ticker, asset_id, amount = self._prepare_lock_params(
                order, order.price, order_asset_id, payment_asset_id
            )
        else:
            price = await self._get_market_quote(order)
            ticker, asset_id, amount = self._prepare_lock_params(
                order, price, order_asset_id, payment_asset_id, is_total_price=True
            )

        await self._lock_assets(user_id, ticker, asset_id, amount)

        order_entity = Order(
            user_id=user_id,
            status=StatusOrder.NEW,
            direction=order.direction,
            qty=order.qty,
            price=order.price,
            order_asset_id=order_asset_id,
            payment_asset_id=payment_asset_id,
        )
        order_entity = await self.order_repo.create(order_entity)

        try:
            await self.order_producer.send_order(order.ticker, order.payment_ticker, order=order_entity)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка отправки ордера в Matching Engine: {e}")
        await asyncio.sleep(0.5)
        return OrderCreateResponse(success=True, order_id=order_entity.id)

    async def cancel_order(
        self,
        user_id: UUID,
        order_id: UUID,
    ) -> OrderCancelResponse:
        order = await self.order_repo.get(order_id, user_id)

        if not order:
            raise HTTPException(status_code=404, detail="Такого ордера не существует")

        if order.status == "EXECUTED":
            raise HTTPException(status_code=404, detail="Ордера уже исполнен")
        logger.info(f"orders status - {order.status}")
        await self.order_producer.cancel_order(
            order_id=order_id,
            direction=order.direction,
            order_ticker=order.order_asset.ticker,
            payment_ticker=order.payment_asset.ticker,
        )
        await asyncio.sleep(0.5)
        return OrderCancelResponse(success=True)
    
    async def cancel_all_orders(
        self,
        user_id: UUID,
    ) -> None:
        orders = await self.order_repo.get_list(user_id)

        for order in orders:
            if order.status not in ("EXECUTED", "CANCELLED"):
                await self.order_producer.cancel_order(
                    order_id=order.id,
                    direction=order.direction,
                    order_ticker=order.order_asset.ticker,
                    payment_ticker=order.payment_asset.ticker)


    async def _lock_assets(self, user_id, ticker, asset_id, amount):
        correlation_id = str(uuid.uuid4())
        try:
            await self.lock_assets_producer.lock_assets(
                user_id=user_id,
                asset_id=asset_id,
                ticker=ticker,
                amount=amount,
                correlation_id=correlation_id,
            )
            success = await self._wait_for_lock_confirmation(correlation_id)
            if not success:
                raise HTTPException(status_code=400, detail=f"Недостаточно средств {ticker}")
        
        except HTTPException as e:
            raise e 
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Таймаут ожидания блокировки активов.")
        except Exception as e:
            logger.error(f"Ошибка локации активов: {e}")
            raise HTTPException(status_code=500, detail="Ошибка при попытке локации активов")

    async def _get_market_quote(self, order) -> int:
        correlation_id = str(uuid.uuid4())
        await self.market_quote_producer.send_request(
            correlation_id=correlation_id,
            order_ticker=order.ticker,
            payment_ticker=order.payment_ticker,
            amount=order.qty,
            direction=order.direction,
        )
        result = await self._wait_for_market_quote(correlation_id)
        if result.get("status") != "ok":
            raise HTTPException(status_code=400, detail=result.get("reason", "Не удалось получить цену"))
        if order.direction == "BUY":
            return int(result["amount_to_pay"])
        return int(order.qty)

    def _prepare_lock_params(self, order, price, order_asset_id, payment_asset_id, is_total_price=False):
        is_buy = order.direction == "BUY"
        ticker = order.payment_ticker if is_buy else order.ticker
        asset_id = payment_asset_id if is_buy else order_asset_id
        amount = int(price) if is_total_price and is_buy else (int(order.qty * price) if is_buy else int(order.qty))
        return ticker, asset_id, amount

    async def _wait_for_lock_confirmation(self, correlation_id: str, timeout: int = 5) -> bool:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        lock_futures[correlation_id] = future
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            lock_futures.pop(correlation_id, None)
            return False

    async def _wait_for_market_quote(self, correlation_id: str, timeout: int = 5):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        market_quote_futures[correlation_id] = future
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            market_quote_futures.pop(correlation_id, None)
            raise

    def _build_order_response(self, order: Order) -> OrderResponse:
        from datetime import timezone

        timestamp = order.updated_at
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        common_data = {
            "id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "timestamp": timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
    	}

        if order.price is not None:
            body = LimitOrderSchema(
                direction=order.direction,
                ticker=order.order_asset.ticker,
                qty=order.qty,
                price=order.price,
            )
            return LimitOrderResponse(**common_data, body=body, filled=order.filled)

        else:
            body = MarketOrderSchema(
                direction=order.direction,
                ticker=order.order_asset.ticker,
                qty=order.qty,
            )

            return OrderResponse(**common_data, body=body, filled=order.filled)
