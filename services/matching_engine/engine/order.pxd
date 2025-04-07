cdef class Order:
    cdef public int order_id
    cdef public int user_id
    cdef public str status
    cdef public str type
    cdef public str direction
    cdef public int order_asset_id
    cdef public int payment_asset_id
    cdef public str order_ticker
    cdef public str payment_ticker
    cdef public int price
    cdef public int qty