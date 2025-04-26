# engine/order_book.pxd
from engine.order cimport Order

cdef class OrderBook:
    cdef str ticker_pair_name
    cdef list buy_orders
    cdef list sell_orders

    cdef Order get_order(self, str order_id, str direction)
    cdef void add_order(self, Order order)
    cdef void remove_order(self, str order_id, str direction)
    cdef Order get_best_buy(self)
    cdef Order get_best_sell(self)
    cdef int get_available_sell_liquidity(self)
    cdef int get_available_buy_liquidity(self)
    cdef int calculate_payment_for_buy(self, int amount)
    cdef void log_order_book(self)
    