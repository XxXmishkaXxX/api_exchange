cdef class Order:
    cdef public int order_id
    cdef public int user_id
    cdef public str status
    cdef public str type
    cdef public str direction
    cdef public int ticker_id
    cdef public double price
    cdef public double qty
