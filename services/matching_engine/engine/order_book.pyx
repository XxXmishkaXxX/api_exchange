from engine.order cimport Order
from libc.stdint cimport int64_t
from engine.price_level cimport PriceLevel

cdef class OrderBook:
    def __init__(self, str ticker_pair_name):
        self.ticker_pair_name = ticker_pair_name
        self.buy_orders = []
        self.sell_orders = []
        self.buy_price_levels = {}
        self.sell_price_levels = {}

    cdef Order get_order(self, str order_id, str direction):
        cdef list orders = self.buy_orders if direction == "BUY" else self.sell_orders
        for order in orders:
            if order.order_id == order_id:
                return order
        return None

    cdef void _update_price_levels(self, str direction, int price, int qty_delta):
        cdef dict levels = self.buy_price_levels if direction == "BUY" else self.sell_price_levels
        if price in levels:
            levels[price] += qty_delta
            if levels[price] <= 0:
                del levels[price]
        elif qty_delta > 0:
            levels[price] = qty_delta

    cdef void add_order(self, Order order):
        """Добавляет ордер в книгу заявок и обновляет агрегированный уровень."""
        if order.direction == "BUY":
            self.buy_orders.append(order)
            self.buy_orders.sort(key=lambda o: -o.price)
        else:
            self.sell_orders.append(order)
            self.sell_orders.sort(key=lambda o: o.price)

        self._update_price_levels(order.direction, order.price, order.qty)

    cdef void remove_order(self, str order_id, str direction):
        """Удаляет ордер из книги заявок и обновляет агрегированный уровень."""
        cdef list orders = self.buy_orders if direction == "BUY" else self.sell_orders
        cdef list remaining_orders = []
        cdef Order o
        for o in orders:
            if o.order_id == order_id:
                self._update_price_levels(direction, o.price, -o.qty)
                continue
            remaining_orders.append(o)
        if direction == "BUY":
            self.buy_orders = remaining_orders
        else:
            self.sell_orders = remaining_orders

    cdef void decrease_order_qty(self, Order order, int qty_to_decrease):
        """Уменьшает количество в ордере и обновляет агрегированную ликвидность."""
        if qty_to_decrease <= 0:
            return
        order.qty -= qty_to_decrease
        self._update_price_levels(order.direction, order.price, -qty_to_decrease)
        if order.qty <= 0:
            self.remove_order(order.order_id, order.direction)

    cdef Order get_best_buy(self):
        return self.buy_orders[0] if self.buy_orders else None

    cdef Order get_best_sell(self):
        return self.sell_orders[0] if self.sell_orders else None

    cpdef list get_price_levels(self, str direction):
        cdef dict levels = self.buy_price_levels if direction == "BUY" else self.sell_price_levels
        cdef list prices = sorted(levels.keys(), reverse=(direction == "BUY"))
        cdef list result = []
        cdef int price

        for price in prices:
            result.append(PriceLevel(price=price, qty=levels[price]))

        return result


    cdef int get_available_sell_liquidity(self):
        cdef int total = 0
        for qty in self.sell_price_levels.values():
            total += qty
        return total

    cdef int get_available_buy_liquidity(self):
        cdef int total = 0
        for qty in self.buy_price_levels.values():
            total += qty
        return total

    cdef int calculate_payment_for_buy(self, int amount):
        cdef int remaining = amount
        cdef int cost = 0
        cdef Order order
        for order in self.sell_orders:
            if remaining <= 0:
                break
            tradable = min(remaining, order.qty)
            cost += tradable * order.price
            remaining -= tradable
        return cost if remaining <= 0 else -1

    cpdef dict to_snapshot(self):
        return {
            "symbol": self.ticker_pair_name,
            "buy_orders": [o.to_dict() for o in self.buy_orders],
            "sell_orders": [o.to_dict() for o in self.sell_orders],
        }
