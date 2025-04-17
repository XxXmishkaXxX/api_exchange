from redis import asyncio as aioredis
import json
from engine.order import Order



class AsyncRedisOrderClient:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.redis_client = None

    async def connect(self):
        """Подключаемся к Redis серверу асинхронно."""
        self.redis_client = aioredis.Redis(host=self.redis_host, port=self.redis_port, db=self.redis_db)
        print(f"Подключение к Redis на {self.redis_host}:{self.redis_port} установлено.")

    async def close(self):
        """Закрываем соединение с Redis."""
        await self.redis_client.close()
        print("Соединение с Redis закрыто.")

    async def add_order(self, order):
        """
        Добавляет ордер в Redis асинхронно.
        :param order_id: Идентификатор ордера.
        :param order_data: Данные ордера (обычно в формате словаря).
        :param ticker_pair: Название торговой пары (например, 'BTC/USD').
        """
        key = f"orderbook:{order.order_ticker}/{order.payment_ticker}"
        field = f"{order.direction}:{order.order_id}"
        value = {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "status": order.status,
            "type": order.type,
            "direction": order.direction,
            "order_asset_id": order.order_asset_id,
            "payment_asset_id": order.payment_asset_id,
            "order_ticker": order.order_ticker,
            "payment_ticker": order.payment_ticker,
            "price": order.price,
            "qty": order.qty,
            "filled": order.filled,
        }
        await self.redis_client.hset(key, field, json.dumps(value))

    async def remove_order(self, order_id, ticker_pair, direction):
        """
        Удаляет ордер из Redis асинхронно.
        :param order_id: Идентификатор ордера.
        :param ticker_pair: Название торговой пары (например, 'BTC/USD').
        """
        key = f"orderbook:{ticker_pair}"
        field = f"{direction}:{order_id}"
        await self.redis_client.hdel(key, field)

    async def set_market_data(self, ticker_pair: str, bid_levels: dict, ask_levels: dict):
        key = f"market_snapshot:{ticker_pair}"
        mapping = {
            "bid_levels": json.dumps(bid_levels),
            "ask_levels": json.dumps(ask_levels)
        }
        await self.redis_client.hset(key, mapping=mapping)
        
    async def get_all_order_books(self) -> dict[str, dict[str, dict]]:
        """Возвращает все ордербуки из Redis в формате: {ticker_pair: {order_id: order_data}}"""
        result = {}
        keys = await self.redis_client.keys("orderbook:*")
        for raw_key in keys:
            key = raw_key.decode("utf-8")
            ticker_pair = key.replace("orderbook:", "")
            orders = await self.redis_client.hgetall(key)
            parsed_orders = {field.decode(): json.loads(val) for field, val in orders.items()}
            result[ticker_pair] = parsed_orders
        return result


