import logging
import asyncio
from engine.order cimport Order
from engine.order_book cimport OrderBook

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

cdef class MatchingEngine:
    cdef:
        dict order_books
        object producer

    def __init__(self, producer):
        self.order_books = {}
        self.producer = producer

    async def send_order_status(self, order_id: int, user_id, status: str):
        """Отправка статуса ордера через продюсер"""
        if self.producer:
            message = {"order_id": order_id, "user_id": user_id, "status": status}
            await self.producer.send_order_update(order_id, user_id, status)
            logger.info(f"📤 SENT: {message}")

    cpdef void add_order(self, Order order):
        """Добавляет ордер и запускает процесс исполнения."""
        cdef OrderBook order_book
        if order.ticker_id not in self.order_books:
            self.order_books[order.ticker_id] = OrderBook(order.ticker_id)

        order_book = self.order_books[order.ticker_id]
        order_book.add_order(order)
        self.match_orders(order_book)

    cdef void match_orders(self, OrderBook order_book):
        """Сопоставляет заявки, если возможно."""
        cdef Order best_buy
        cdef Order best_sell
        cdef double trade_qty

        while True:
            best_buy = order_book.get_best_buy()
            best_sell = order_book.get_best_sell()

            if not best_buy or not best_sell or best_buy.price < best_sell.price:
                break

            trade_qty = min(best_buy.qty, best_sell.qty)
            best_buy.qty -= trade_qty
            best_sell.qty -= trade_qty

            logger.info(f"🔄 TRADE EXECUTED: {trade_qty:.2f} @ {best_sell.price:.2f}")

            if best_buy.qty == 0:
                asyncio.create_task(self.send_order_status(best_buy.order_id, best_buy.user_id, "filled"))
                order_book.remove_order(best_buy.order_id, best_buy.direction)

            if best_sell.qty == 0:
                asyncio.create_task(self.send_order_status(best_sell.order_id, best_sell.user_id, "filled"))
                order_book.remove_order(best_sell.order_id, best_sell.direction)

    cdef void execute_market_order(self, Order order):
        """Исполняет рыночный ордер, удаляя ордера из стакана."""
        cdef OrderBook order_book
        cdef list orders
        cdef Order best_order
        cdef double trade_qty

        if order.ticker_id not in self.order_books:
            return

        order_book = self.order_books[order.ticker_id]
        orders = order_book.sell_orders if order.direction == "sell" else order_book.buy_orders

        while order.qty > 0 and orders:
            best_order = orders[0]

            trade_qty = min(order.qty, best_order.qty)
            order.qty -= trade_qty
            best_order.qty -= trade_qty

            logger.info(f"✅ MATCHED: {trade_qty:.2f} @ {best_order.price:.2f}")

            if order.qty == 0:
                asyncio.create_task(self.send_order_status(order.order_id, order.user_id, "filled"))

            if best_order.qty == 0:
                asyncio.create_task(self.send_order_status(best_order.order_id, best_order.user_id, "filled"))
                orders.pop(0)
