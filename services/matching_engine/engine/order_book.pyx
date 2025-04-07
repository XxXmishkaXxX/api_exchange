from engine.order cimport Order
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cdef class OrderBook:
    def __init__(self, str ticker_pair_name):
        self.ticker_pair_name = ticker_pair_name
        self.buy_orders = []
        self.sell_orders = []

    cdef void add_order(self, Order order):
        """Добавляет ордер в книгу заявок."""
        if order.direction == "buy":  # Покупка
            self.buy_orders.append(order)
            self.buy_orders.sort(key=lambda o: -o.price)  # По убыванию цены
        else:
            self.sell_orders.append(order)
            self.sell_orders.sort(key=lambda o: o.price)  # По возрастанию цены

    cdef void remove_order(self, int order_id, direction: str):
        """Удаляет ордер из книги заявок."""
        cdef list orders = self.buy_orders if direction == "buy" else self.sell_orders
        orders[:] = [o for o in orders if o.order_id != order_id]

    cdef Order get_best_buy(self):
        """Возвращает лучший ордер на покупку."""
        return self.buy_orders[0] if self.buy_orders else None  # FIXED

    cdef Order get_best_sell(self):
        """Возвращает лучший ордер на продажу."""
        return self.sell_orders[0] if self.sell_orders else None  # FIXED

    cdef void log_order_book(self):
        """Логирует текущее состояние книги заявок."""
        logger.info(f"OrderBook {self.ticker_id} - Buy Orders: {self.buy_orders}, Sell Orders: {self.sell_orders}")