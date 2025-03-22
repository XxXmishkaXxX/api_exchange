import logging
from engine.order import Order
from engine.order_book import OrderBook

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MatchingEngine:
    def __init__(self):
        self.order_books = {}

    def add_order(self, order: Order):
        logger.info(f"\n📌 NEW ORDER ADDED: {order.order_id}, {order.type}, {order.direction}, {order.ticker_id}, {order.price:.2f}, {order.qty:.2f}")
        if order.ticker_id not in self.order_books:
            self.order_books[order.ticker_id] = OrderBook(order.ticker_id)
        order_book = self.order_books[order.ticker_id]
        if order.type == "market":
            order_book.execute_market_order(order)
        else:
            order_book.add_order(order)
        order_book.match_orders()
        order_book.log_order_book()