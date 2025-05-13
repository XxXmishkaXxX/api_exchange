import json
from engine.order cimport Order
from engine.order_book cimport OrderBook

cdef class OrderLogReplayer:
    cdef str filepath
    cdef int snapshot_timestamp

    def __init__(self, filepath: str, snapshot_timestamp: int):
        self.filepath = filepath
        self.snapshot_timestamp = snapshot_timestamp

    cpdef void truncate_before_snapshot(self):
        cdef list filtered_lines = []
        cdef dict event
        cdef int event_timestamp

        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                event = json.loads(line)
                event_timestamp = event["timestamp"]
                if event_timestamp >= self.snapshot_timestamp:
                    filtered_lines.append(line)

        with open(self.filepath, "w", encoding="utf-8") as f:
            f.writelines(filtered_lines)

    cpdef void replay(self, dict books):
        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                event = json.loads(line)
                event_timestamp = event["timestamp"]
                self._apply_event(books, event)

    cdef void _apply_event(self, dict books, dict event):
        cdef OrderBook book
        cdef str action
        cdef str symbol
        cdef Order order, update_order, existing
        cdef object book_obj
        cdef str order_id

        action = event["action"]

        if action == "add":
            order = Order.from_dict(event["order"])
            symbol = order.order_ticker + "/" + order.payment_ticker
            book = <OrderBook>books[symbol]
            book.add_order(order)

        elif action == "remove":
            order_id = event["order_id"]
            direction = event["direction"]
            for book_obj in books.values():
                book = <OrderBook>book_obj
                book.remove_order(order_id, direction)

        elif action == "update":
            update_order = Order.from_dict(event["order"])
            symbol = update_order.order_ticker + "/" + update_order.payment_ticker
            book = <OrderBook>books[symbol]
            existing = book.get_order(update_order.order_id, update_order.direction)

            if existing is not None:
                existing.price = update_order.price
                existing.qty = update_order.qty
