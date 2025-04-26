from engine.order cimport Order
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cdef class OrderBook:
    def __init__(self, str ticker_pair_name):
        self.ticker_pair_name = ticker_pair_name
        self.buy_orders = []
        self.sell_orders = []

    cdef Order get_order(self, str order_id, str direction):
        cdef list orders = self.buy_orders if direction == "buy" else self.sell_orders
        for order in orders:
            if order.order_id == order_id:
                return order
        return None

    cdef void add_order(self, Order order):
        """Добавляет ордер в книгу заявок."""
        if order.direction == "buy":
            self.buy_orders.append(order)
            self.buy_orders.sort(key=lambda o: -o.price)
        else:
            self.sell_orders.append(order)
            self.sell_orders.sort(key=lambda o: o.price)

    cdef void remove_order(self, str order_id, direction: str):
        """Удаляет ордер из книги заявок."""
        cdef list orders = self.buy_orders if direction == "buy" else self.sell_orders
        orders[:] = [o for o in orders if o.order_id != order_id]

    cdef Order get_best_buy(self):
        """Возвращает лучший ордер на покупку."""
        return self.buy_orders[0] if self.buy_orders else None

    cdef Order get_best_sell(self):
        """Возвращает лучший ордер на продажу."""
        return self.sell_orders[0] if self.sell_orders else None
    
    cdef int get_available_sell_liquidity(self):
        """Возвращает общую доступную ликвидность на продажу (сколько можно купить)."""
        cdef int total = 0
        for order in self.sell_orders:
            total += order.qty
        return total

    cdef int get_available_buy_liquidity(self):
        """Возвращает общую доступную ликвидность на покупку (сколько можно продать)."""
        cdef int total = 0
        for order in self.buy_orders:
            total += order.qty
        return total

    cdef int calculate_payment_for_buy(self, int amount):
        """
        Рассчитывает, сколько нужно заплатить за покупку `amount` актива,
        проходясь по лучшим ордерам на продажу.
        """
        cdef int remaining = amount
        cdef int cost = 0
        for order in self.sell_orders:
            if remaining <= 0:
                break
            tradable = min(remaining, order.qty)
            cost += tradable * order.price
            remaining -= tradable
        return cost if remaining <= 0 else -1

    cdef void log_order_book(self):
        """Логирует текущее состояние книги заявок."""
        buy_orders_info = [{"order_id": o.order_id, "price": o.price, "qty": o.qty} for o in self.buy_orders]
        sell_orders_info = [{"order_id": o.order_id, "price": o.price, "qty": o.qty} for o in self.sell_orders]
        logger.info(f"OrderBook {self.ticker_pair_name} - Buy Orders: {buy_orders_info}, Sell Orders: {sell_orders_info}")
