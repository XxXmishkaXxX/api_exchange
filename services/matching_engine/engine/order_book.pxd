# engine/order_book.pxd
from engine.order cimport Order

cdef class OrderBook:
    cdef int ticker_id
    cdef list buy_orders
    cdef list sell_orders

    cdef void add_order(self, Order order)
    cdef void remove_order(self, int order_id, str direction)
    cdef Order get_best_buy(self)
    cdef Order get_best_sell(self)
    cdef void log_order_book(self)