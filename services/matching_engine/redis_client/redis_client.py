from redis import Redis
import json
from engine.order import Order


class RedisOrderClient:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = Redis.from_url(self.redis_url, decode_responses=True)

    def close(self):
        """Закрываем соединение с Redis."""
        self.redis_client.close()

    def add_order(self, order: Order):
        """
        Добавляет ордер в Redis синхронно.
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
        self.redis_client.hset(key, field, json.dumps(value))

    def remove_order(self, order_id: str, ticker_pair: str, direction: str):
        """
        Удаляет ордер из Redis синхронно.
        """
        key = f"orderbook:{ticker_pair}"
        field = f"{direction}:{order_id}"
        self.redis_client.hdel(key, field)

    def set_market_data(self, ticker_pair: str, bid_levels: dict, ask_levels: dict):
        """
        Сохраняет рыночные данные в Redis.
        """
        key = f"market_snapshot:{ticker_pair}"
        mapping = {
            "bid_levels": json.dumps(bid_levels),
            "ask_levels": json.dumps(ask_levels)
        }
        self.redis_client.hset(key, mapping=mapping)

    def get_all_order_books(self) -> dict[str, dict[str, dict]]:
        """
        Возвращает все ордербуки из Redis.
        """
        result = {}
        keys = self.redis_client.keys("orderbook:*")
        for key in keys:
            ticker_pair = key.replace("orderbook:", "")
            orders = self.redis_client.hgetall(key)
            parsed_orders = {field: json.loads(val) for field, val in orders.items()}
            result[ticker_pair] = parsed_orders
        return result
