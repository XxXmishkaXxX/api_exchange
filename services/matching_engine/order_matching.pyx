from libc.stdlib cimport malloc, free
from collections import defaultdict
from heapq import heappush, heappop
from kafka import KafkaConsumer, KafkaProducer
import json

# ==============================
# 1. Определяем Enum'ы как строки
# ==============================
DEF BUY = "buy"
DEF SELL = "sell"

DEF MARKET = "market"
DEF LIMIT = "limit"

DEF NEW = "new"
DEF FILLED = "filled"
DEF PENDING = "pending"
DEF REJECTED = "rejected"

# ==============================
# 2. Определяем структуру ордера
# ==============================
cdef struct Order:
    int id
    int user_id
    char* type  # Тип ордера (MARKET или LIMIT)
    char* status
    char* direction  # Направление ордера (BUY или SELL)
    int ticker_id
    int qty
    double price  # Цена для LIMIT ордера

# ==============================
# 3. Класс OrderBook (хранит ордера по тикерам)
# ==============================
cdef class OrderBook:
    cdef:
        dict order_books  # {ticker_id: (buy_orders, sell_orders)}

    def __init__(self):
        self.order_books = defaultdict(lambda: ([], []))  # {ticker: (BID[], ASK[])}

    # Добавить ордер в книгу
    cdef void add_order(self, Order order):
        buy_orders, sell_orders = self.order_books[order.ticker_id]
        if order.direction == BUY:
            heappush(buy_orders, (-order.price, order))  # BID → max heap
        else:
            heappush(sell_orders, (order.price, order))  # ASK → min heap

    # Попытка сматчить ордера
    cdef list match_orders(self, int ticker_id):
        buy_orders, sell_orders = self.order_books[ticker_id]
        matched_trades = []

        while buy_orders and sell_orders:
            cdef tuple buy_tuple = heappop(buy_orders)
            cdef tuple sell_tuple = heappop(sell_orders)

            cdef Order buy_order = buy_tuple[1]
            cdef Order sell_order = sell_tuple[1]

            # Проверяем, можно ли исполнить сделку
            if -buy_tuple[0] >= sell_tuple[0]:
                trade_qty = min(buy_order.qty, sell_order.qty)

                # Формируем результат сделки
                trade = {
                    "buyer": buy_order.user_id,
                    "seller": sell_order.user_id,
                    "ticker_id": ticker_id,
                    "price": sell_tuple[0],
                    "quantity": trade_qty
                }
                matched_trades.append(trade)

                # Обновляем статусы
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
    cdef list match_market_orders(self, int ticker_id):
        buy_orders, sell_orders = self.order_books[ticker_id]
        matched_trades = []

        # Обрабатываем рыночные ордера
        cdef list market_orders = []

        for order in buy_orders:
            if order[1].type == MARKET:
                market_orders.append(order[1])

        for order in sell_orders:
            if order[1].type == MARKET:
                market_orders.append(order[1])

        # Обрабатываем рыночные ордера
        for order in market_orders:
            if order.direction == BUY:
                if sell_orders:
                    cdef tuple sell_tuple = heappop(sell_orders)
                    cdef Order sell_order = sell_tuple[1]
                    trade_qty = min(order.qty, sell_order.qty)
                    trade = {
                        "buyer": order.user_id,
                        "seller": sell_order.user_id,
                        "ticker_id": ticker_id,
                        "price": sell_tuple[0],
                        "quantity": trade_qty
                    }
                    matched_trades.append(trade)

                    # Обновляем статусы ордеров
                    if sell_order.qty > trade_qty:
                        sell_order.qty -= trade_qty
                        sell_order.status = PENDING
                        heappush(sell_orders, (sell_tuple[0], sell_order))
                    else:
                        sell_order.status = FILLED
            elif order.direction == SELL:
                if buy_orders:
                    cdef tuple buy_tuple = heappop(buy_orders)
                    cdef Order buy_order = buy_tuple[1]
                    trade_qty = min(order.qty, buy_order.qty)
                    trade = {
                        "buyer": buy_order.user_id,
                        "seller": order.user_id,
                        "ticker_id": ticker_id,
                        "price": buy_tuple[0],
                        "quantity": trade_qty
                    }
                    matched_trades.append(trade)

                    # Обновляем статусы ордеров
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
        self.consumer = KafkaConsumer('orders-in', bootstrap_servers='localhost:9092', group_id='matcher')
        self.producer = KafkaProducer(bootstrap_servers='localhost:9092')

    # Запуск движка
    def run(self):
        for message in self.consumer:
            order_data = json.loads(message.value)
            cdef Order order = Order(
                id=order_data["id"],
                user_id=order_data["user_id"],
                type=order_data["type"].encode(),
                status=NEW.encode(),
                direction=order_data["direction"].encode(),
                ticker_id=order_data["ticker_id"],
                qty=order_data["qty"],
                price=order_data["price"] if order_data["price"] is not None else 0.0
            )

            self.order_book.add_order(order)

            if order.type == MARKET:
                trades = self.order_book.match_market_orders(order.ticker_id)
            else:
                trades = self.order_book.match_orders(order.ticker_id)

            # Если сделки состоялись, отправляем в Kafka
            if trades:
                self.producer.send('trades-out', json.dumps(trades).encode())

# ==============================
# 5. Запуск Matching Engine
# ==============================
if __name__ == "__main__":
    engine = MatchingEngine()
    engine.run()
