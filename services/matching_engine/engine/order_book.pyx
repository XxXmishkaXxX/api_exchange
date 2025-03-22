import logging
from heapq import heappush, heappop
from engine.order import Order

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class OrderBook:
    def __init__(self, ticker_id):
        self.ticker_id = ticker_id
        self.buy_orders = []
        self.sell_orders = []

    def add_order(self, order: Order):
        if order.direction == "buy":
            heappush(self.buy_orders, (-order.price, order.order_id, order))
        else:
            heappush(self.sell_orders, (order.price, order.order_id, order))

    def match_orders(self):
        while self.buy_orders and self.sell_orders:
            buy_price, _, buy_order = self.buy_orders[0]
            sell_price, _, sell_order = self.sell_orders[0]

            if -buy_price >= sell_price:
                trade_qty = min(buy_order.qty, sell_order.qty)
                buy_order.qty -= trade_qty
                sell_order.qty -= trade_qty
                logger.info(f"\n🔄 TRADE EXECUTED: {trade_qty:.2f} @ {sell_price:.2f}")

                if buy_order.qty == 0:
                    heappop(self.buy_orders)
                if sell_order.qty == 0:
                    heappop(self.sell_orders)
            else:
                break

    def execute_market_order(self, order: Order):
        if order.direction == "buy":
            while order.qty > 0 and self.sell_orders:
                sell_price, _, sell_order = heappop(self.sell_orders)
                trade_qty = min(order.qty, sell_order.qty)
                order.qty -= trade_qty
                sell_order.qty -= trade_qty
                logger.info(f"✅ MATCHED: {trade_qty:.2f} @ {sell_price:.2f}")
                if sell_order.qty > 0:
                    heappush(self.sell_orders, (sell_price, sell_order.order_id, sell_order))
        else:
            while order.qty > 0 and self.buy_orders:
                buy_price, _, buy_order = heappop(self.buy_orders)
                trade_qty = min(order.qty, buy_order.qty)
                order.qty -= trade_qty
                buy_order.qty -= trade_qty
                logger.info(f"✅ MATCHED: {trade_qty:.2f} @ {-buy_price:.2f}")
                if buy_order.qty > 0:
                    heappush(self.buy_orders, (buy_price, buy_order.order_id, buy_order))

    def log_order_book(self):
        logger.info("\n📊 ORDER BOOK STATUS")
        logger.info(f"┌ Ticker: {self.ticker_id}")
        logger.info("├ BUY ORDERS:")
        for p, _, o in sorted(self.buy_orders, reverse=True):
            logger.info(f"│  → {o.qty:.2f} @ {-p:.2f} (Order ID: {o.order_id})")
        logger.info("├ SELL ORDERS:")
        for p, _, o in sorted(self.sell_orders):
            logger.info(f"│  → {o.qty:.2f} @ {p:.2f} (Order ID: {o.order_id})")
        logger.info("└───────────────")