from libc.stdlib cimport malloc, free
from collections import defaultdict
from heapq import heappush, heappop
from kafka import KafkaConsumer, KafkaProducer
import json

# ==============================
# 1. Определяем Enum'ы как строки
# ==============================
BUY = "buy"
SELL = "sell"

MARKET = "market"
LIMIT = "limit"

NEW = "new"
FILLED = "filled"
PENDING = "pending"
REJECTED = "rejected"

# ==============================
# 2. Определяем структуру ордера
# ==============================
cdef class Order:
    cdef int id
    cdef int user_id
    cdef str type  # Тип ордера (MARKET или LIMIT)
    cdef str status
    cdef str direction  # Направление ордера (BUY или SELL)
    cdef int ticker_id
    cdef int qty
    cdef double price  # Цена для LIMIT ордера

    def __init__(self, int id, int user_id, str type, str status, str direction, int ticker_id, int qty, double price):
        self.id = id
        self.user_id = user_id
        self.type = type
        self.status = status
        self.direction = direction
        self.ticker_id = ticker_id
        self.qty = qty
        self.price = price

# ==============================
# 3. Класс OrderBook (хранит ордера по тикерам)
# ==============================
cdef class OrderBook:
    cdef:
        dict order_books  # {ticker_id: (buy_orders, sell_orders)}

    def __init__(self):
        self.order_books = defaultdict(lambda: ([], []))  # {ticker: (BID[], ASK[])}

    # Добавить ордер в книгу
    def add_order(self, Order order):
        buy_orders, sell_orders = self.order_books[order.ticker_id]
        if order.direction == BUY:
            heappush(buy_orders, (-order.price, order))  # BID → max heap
        else:
            heappush(sell_orders, (order.price, order))  # ASK → min heap

    # Попытка сматчить ордера
    def match_orders(self, int ticker_id):
        buy_orders, sell_orders = self.order_books[ticker_id]
        matched_trades = []

        # Объявляем переменные в начале метода
        cdef tuple buy_tuple
        cdef tuple sell_tuple
        cdef Order buy_order
        cdef Order sell_order

        while buy_orders and sell_orders:
            buy_tuple = heappop(buy_orders)
            sell_tuple = heappop(sell_orders)

            buy_order = buy_tuple[1]
            sell_order = sell_tuple[1]

            if -buy_tuple[0] >= sell_tuple[0]:
                trade_qty = min(buy_order.qty, sell_order.qty)

                trade = {
                    "buyer": buy_order.user_id,
                    "seller": sell_order.user_id,
                    "ticker_id": ticker_id,
                    "price": sell_tuple[0],
                    "quantity": trade_qty
                }
                matched_trades.append(trade)

                if buy_order.qty > trade_qty:
                    buy_order.qty -= trade_qty
                    buy_order.status = PENDING
                    heappush(buy_orders, (buy_tuple[0], buy_order))
                else:
                    buy_order.status = FILLED

                if sell_order.qty > trade_qty:
                    sell_order.qty -= trade_qty
                    sell_order.status = PENDING
                    heappush(sell_orders, (sell_tuple[0], sell_order))
                else:
                    sell_order.status = FILLED
            else:
                heappush(buy_orders, buy_tuple)
                heappush(sell_orders, sell_tuple)
                break

        return matched_trades


    # Обработка рыночных ордеров
    def match_market_orders(self, int ticker_id):
        buy_orders, sell_orders = self.order_books[ticker_id]
        matched_trades = []

        # Объявляем Cython-переменные в начале метода
        cdef list market_orders = []
        cdef tuple sell_tuple
        cdef tuple buy_tuple
        cdef Order sell_order
        cdef Order buy_order
        cdef int trade_qty

        for order in buy_orders:
            if order[1].type == MARKET:
                market_orders.append(order[1])

        for order in sell_orders:
            if order[1].type == MARKET:
                market_orders.append(order[1])

        for order in market_orders:
            if order.direction == BUY:
                if sell_orders:
                    sell_tuple = heappop(sell_orders)
                    sell_order = sell_tuple[1]
                    trade_qty = min(order.qty, sell_order.qty)
                    trade = {
                        "buyer": order.user_id,
                        "seller": sell_order.user_id,
                        "ticker_id": ticker_id,
                        "price": sell_tuple[0],
                        "quantity": trade_qty
                    }
                    matched_trades.append(trade)

                    if sell_order.qty > trade_qty:
                        sell_order.qty -= trade_qty
                        sell_order.status = PENDING
                        heappush(sell_orders, (sell_tuple[0], sell_order))
                    else:
                        sell_order.status = FILLED

            elif order.direction == SELL:
                if buy_orders:
                    buy_tuple = heappop(buy_orders)
                    buy_order = buy_tuple[1]
                    trade_qty = min(order.qty, buy_order.qty)
                    trade = {
                        "buyer": buy_order.user_id,
                        "seller": order.user_id,
                        "ticker_id": ticker_id,
                        "price": buy_tuple[0],
                        "quantity": trade_qty
                    }
                    matched_trades.append(trade)

                    if buy_order.qty > trade_qty:
                        buy_order.qty -= trade_qty
                        buy_order.status = PENDING
                        heappush(buy_orders, (buy_tuple[0], buy_order))
                    else:
                        buy_order.status = FILLED

        return matched_trades


# ==============================
# 4. Matching Engine (работает с Kafka)
# ==============================
cdef class MatchingEngine:
    cdef:
        OrderBook order_book
        object producer
        object consumer

    def __init__(self):
        self.order_book = OrderBook()
        self.consumer = KafkaConsumer('orders', bootstrap_servers='kafka:9092', group_id='matcher')
        self.producer = KafkaProducer(bootstrap_servers='kafka:9092')

    # Запуск движка
    def run(self):
        cdef Order order  # Объявляем заранее Cython-класс

        for message in self.consumer:
            order_data = json.loads(message.value)
            order = Order(
                id=order_data["id"],
                user_id=order_data["user_id"],
                type=order_data["type"],
                status=NEW,
                direction=order_data["direction"],
                ticker_id=order_data["ticker_id"],
                qty=order_data["qty"],
                price=order_data["price"] if order_data["price"] is not None else 0.0
            )

            self.order_book.add_order(order)

            if order.type == MARKET:
                trades = self.order_book.match_market_orders(order.ticker_id)
            else:
                trades = self.order_book.match_orders(order.ticker_id)

            if trades:
                self.producer.send('trades-out', json.dumps(trades).encode())


# ==============================
# 5. Запуск Matching Engine
# ==============================
if __name__ == "__main__":
    engine = MatchingEngine()
    engine.run()
