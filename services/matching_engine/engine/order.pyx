cdef class Order:
    def __init__(self, int order_id, int user_id, str status, str type, str direction, int ticker_id, double price, double qty):
        self.order_id = order_id
        self.user_id = user_id
        self.status = status
        self.type = type
        self.direction = direction
        self.ticker_id = ticker_id
        self.price = price if price is not None else 0.0
        self.qty = qty