# distutils: language = c
# cython: boundscheck=False, wraparound=False, nonecheck=False

import asyncio
from aiokafka import AIOKafkaConsumer
from heapq import heappush, heappop
from collections import deque

cdef class Order:
    cdef str order_id
    cdef str side  # "buy" or "sell"
    cdef double price
    cdef double quantity
    
    def __init__(self, str order_id, str side, double price, double quantity):
        self.order_id = order_id
        self.side = side
        self.price = price
        self.quantity = quantity

cdef class MatchingEngine:
    cdef list buy_orders  # Мин-куча для продаж
    cdef list sell_orders  # Макс-куча для покупок
    cdef dict order_book
    
    def __init__(self):
        self.buy_orders = []
        self.sell_orders = []
        self.order_book = {}
    
    cpdef void add_order(self, Order order):
        if order.side == "buy":
            heappush(self.buy_orders, (-order.price, order))
        else:
            heappush(self.sell_orders, (order.price, order))
        self.order_book[order.order_id] = order
        self.match_orders()
    
    cpdef void match_orders(self):
        while self.buy_orders and self.sell_orders:
            buy_price, buy_order = self.buy_orders[0]
            sell_price, sell_order = self.sell_orders[0]
            
            if -buy_price >= sell_price:
                trade_qty = min(buy_order.quantity, sell_order.quantity)
                buy_order.quantity -= trade_qty
                sell_order.quantity -= trade_qty
                
                if buy_order.quantity == 0:
                    heappop(self.buy_orders)
                if sell_order.quantity == 0:
                    heappop(self.sell_orders)
            else:
                break

async def consume_orders():
    consumer = AIOKafkaConsumer(
        "orders",
        bootstrap_servers="kafka:9092"
    )
    await consumer.start()
    engine = MatchingEngine()
    try:
        async for msg in consumer:
            data = msg.value.decode("utf-8").split(",")
            order = Order(data[0], data[1], float(data[2]), float(data[3]))
            engine.add_order(order)
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume_orders())
