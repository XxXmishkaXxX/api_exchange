cdef class Order:
    def __init__(self,
                 str order_id,
                 str user_id,
                 str status,
                 str type,
                 str direction,
                 int order_asset_id,
                 int payment_asset_id,
                 str order_ticker,
                 str payment_ticker,
                 int price,
                 int qty,
                 int filled):
        self.order_id = order_id
        self.user_id = user_id
        self.status = status
        self.type = type
        self.direction = direction
        self.order_asset_id = order_asset_id
        self.payment_asset_id = payment_asset_id
        self.order_ticker = order_ticker
        self.payment_ticker = payment_ticker
        self.price = price if price is not None else 0
        self.qty = qty
        self.filled = filled