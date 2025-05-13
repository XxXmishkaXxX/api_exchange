cdef class Order:
    cdef public str order_id
    cdef public str user_id
    cdef public str status
    cdef public str type
    cdef public str direction
    cdef public int order_asset_id
    cdef public int payment_asset_id
    cdef public str order_ticker
    cdef public str payment_ticker
    cdef public int price
    cdef public int qty
    cdef public int filled
    cpdef dict to_dict(self)
    @staticmethod
    cdef Order from_dict(dict d)