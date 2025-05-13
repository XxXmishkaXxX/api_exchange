import json
import time
import os
from engine.order_book cimport OrderBook
from engine.order cimport Order
from core.loggers.system_logger import logger

cdef class SnapshotManager:
    cdef:
        public dict books
        str filepath

    def __init__(self, dict books, str filepath):
        self.books = books
        self.filepath = filepath

        snapshot_dir = os.path.dirname(self.filepath)
        if not os.path.exists(snapshot_dir):
            try:
                os.makedirs(snapshot_dir)
                logger.info(f"Created directory for snapshots: {snapshot_dir}")
            except Exception as e:
                logger.error(f"Failed to create directory for snapshots: {e}")

    cpdef void save_snapshot(self):
        cdef dict snapshot = {
            "timestamp": int(time.time()),
            "orderbooks": {
                symbol: book.to_snapshot() for symbol, book in self.books.items()
            }
        }

        try:
            with open(self.filepath, "w") as f:
                json.dump(snapshot, f, indent=4)
            logger.info(f"Snapshot saved successfully to {self.filepath}")
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")

    cpdef tuple load_snapshot(self):
        cdef dict restored_books = {}

        if not os.path.exists(self.filepath):
            logger.warning(f"Snapshot file not found: {self.filepath}. Returning empty order books.")
            return {}, 0

        cdef dict snapshot

        try:
            with open(self.filepath, "r") as f:
                snapshot = json.load(f)
            logger.info(f"Snapshot loaded successfully from {self.filepath}")
        except Exception as e:
            logger.error(f"Failed to load snapshot from {self.filepath}: {e}")
            return {}, 0

        for symbol, book_data in snapshot.get("orderbooks", {}).items():
            book = OrderBook(symbol)
            for od in book_data.get("buy_orders", []):
                book.add_order(Order.from_dict(od))
            for od in book_data.get("sell_orders", []):
                book.add_order(Order.from_dict(od))
            restored_books[symbol] = book

        return restored_books, snapshot.get("timestamp", 0)
