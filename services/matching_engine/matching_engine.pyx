import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from heapq import heappush, heappop

# Настройка логирования с форматированием
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Класс ордера на Cython
cdef class Order:
    cdef public int order_id
    cdef public int user_id
    cdef public str status
    cdef public str type
    cdef public str direction
    cdef public int ticker_id
    cdef public double price
    cdef public double qty

    def __init__(self, int order_id, int user_id, str status, str type, str direction, int ticker_id, double price, double qty):
        self.order_id = order_id
        self.user_id = user_id
        self.status = status
        self.type = type
        self.direction = direction
        self.ticker_id = ticker_id
        self.price = price if price is not None else 0.0
        self.qty = qty

# Механизм сопоставления ордеров
cdef class MatchingEngine:
    cdef dict order_books  # {ticker_id: (buy_heap, sell_heap)}

    def __init__(self):
        self.order_books = {}

    cpdef void add_order(self, Order order):
        logger.info("\n📌 NEW ORDER ADDED")
        logger.info(f"┌ Order ID: {order.order_id}")
        logger.info(f"├ Type: {order.type.upper()} | Direction: {order.direction.upper()}")
        logger.info(f"├ User ID: {order.user_id} | Ticker: {order.ticker_id}")
        logger.info(f"└ Price: {order.price:.2f} | Quantity: {order.qty:.2f}")

        if order.ticker_id not in self.order_books:
            self.order_books[order.ticker_id] = ([], [])

        buy_orders, sell_orders = self.order_books[order.ticker_id]

        if order.type == "market":
            self.execute_market_order(order, buy_orders, sell_orders)
        else:
            if order.direction == "buy":
                heappush(buy_orders, (-order.price, order.order_id, order))  # Инвертируем цену для max-heap
            else:
                heappush(sell_orders, (order.price, order.order_id, order))

        self.match_orders(order.ticker_id)
        self.log_order_book(order.ticker_id)

    cpdef void execute_market_order(self, Order order, list buy_orders, list sell_orders):
        logger.info("\n⚡ EXECUTING MARKET ORDER")
        logger.info(f"┌ Order ID: {order.order_id}")
        logger.info(f"├ Type: {order.type.upper()} | Direction: {order.direction.upper()}")
        logger.info(f"└ Quantity: {order.qty:.2f}")

        if order.direction == "buy":
            while order.qty > 0 and sell_orders:
                sell_price, _, sell_order = heappop(sell_orders)
                trade_qty = min(order.qty, sell_order.qty)
                order.qty -= trade_qty
                sell_order.qty -= trade_qty
                logger.info(f"✅ MATCHED: {trade_qty:.2f} @ {sell_price:.2f}")

                if sell_order.qty > 0:
                    heappush(sell_orders, (sell_price, sell_order.order_id, sell_order))
        else:
            while order.qty > 0 and buy_orders:
                buy_price, _, buy_order = heappop(buy_orders)
                trade_qty = min(order.qty, buy_order.qty)
                order.qty -= trade_qty
                buy_order.qty -= trade_qty
                logger.info(f"✅ MATCHED: {trade_qty:.2f} @ {-buy_price:.2f}")

                if buy_order.qty > 0:
                    heappush(buy_orders, (buy_price, buy_order.order_id, buy_order))

    cpdef void match_orders(self, int ticker_id):
        buy_orders, sell_orders = self.order_books[ticker_id]

        while buy_orders and sell_orders:
            buy_price, _, buy_order = buy_orders[0]
            sell_price, _, sell_order = sell_orders[0]

            if -buy_price >= sell_price:
                trade_qty = min(buy_order.qty, sell_order.qty)
                buy_order.qty -= trade_qty
                sell_order.qty -= trade_qty
                logger.info(f"\n🔄 TRADE EXECUTED: {trade_qty:.2f} @ {sell_price:.2f}")

                if buy_order.qty == 0:
                    heappop(buy_orders)
                if sell_order.qty == 0:
                    heappop(sell_orders)
            else:
                break

        self.log_order_book(ticker_id)

    cpdef log_order_book(self, int ticker_id):
        """ Логирует текущее состояние стакана заявок красиво. """
        buy_orders, sell_orders = self.order_books[ticker_id]

        logger.info("\n📊 ORDER BOOK STATUS")
        logger.info(f"┌ Ticker: {ticker_id}")

        # Buy Orders (Инвертируем цену для вывода в нормальном виде)
        logger.info("├ BUY ORDERS:")
        for p, _, o in sorted(buy_orders, reverse=True):
            logger.info(f"│  → {o.qty:.2f} @ {-p:.2f} (Order ID: {o.order_id})")

        # Sell Orders
        logger.info("├ SELL ORDERS:")
        for p, _, o in sorted(sell_orders):
            logger.info(f"│  → {o.qty:.2f} @ {p:.2f} (Order ID: {o.order_id})")

        logger.info("└───────────────")

# Асинхронный потребитель Kafka
async def consume_orders():
    consumer = AIOKafkaConsumer(
        "orders",  # Название топика Kafka
        bootstrap_servers="kafka:9092"
    )
    await consumer.start()
    engine = MatchingEngine()

    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode("utf-8"))
            logger.info("\n📩 RECEIVED ORDER MESSAGE")
            logger.info(f"┌ {data}")

            order = Order(
                order_id=int(data["order_id"]),
                user_id=int(data["user_id"]),
                status=data["status"],
                type=data["type"],
                direction=data["direction"],
                ticker_id=int(data["ticker_id"]),
                price=float(data["price"]) if "price" in data and data["price"] is not None else 0.0,
                qty=float(data["qty"])
            )

            engine.add_order(order)
    except Exception as e:
        logger.error(f"❌ Error consuming message: {e}")
    finally:
        await consumer.stop()
        logger.info("\n🔻 Kafka consumer stopped")

# Главная асинхронная функция для запуска
if __name__ == "__main__":
    try:
        asyncio.run(consume_orders())
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
