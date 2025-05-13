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
    
    @staticmethod
    cdef Order from_dict(dict d):
        return Order(
            d.get("order_id", ""),
            d.get("user_id", ""),
            d.get("status", ""),
            d.get("type", ""),
            d.get("direction", ""),
            d.get("order_asset_id", 0),
            d.get("payment_asset_id", 0),
            d.get("order_ticker", ""),
            d.get("payment_ticker", ""),
            d.get("price", 0),
            d.get("qty", 0),
            d.get("filled", 0),
        )

    cpdef dict to_dict(self):
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "status": self.status,
            "type": self.type,
            "direction": self.direction,
            "order_asset_id": self.order_asset_id,
            "payment_asset_id": self.payment_asset_id,
            "order_ticker": self.order_ticker,
            "payment_ticker": self.payment_ticker,
            "price": self.price,
            "qty": self.qty,
            "filled": self.filled
        }
