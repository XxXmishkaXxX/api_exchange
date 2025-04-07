import logging
import asyncio
from engine.order cimport Order
from engine.order_book cimport OrderBook

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

cdef class MatchingEngine:
    cdef:
        dict order_books
        object change_order_status_prod
        object post_wallet_transfer_prod

    def __init__(self, change_order_status_prod, post_wallet_transfer_prod):
        self.order_books = {}
        self.post_wallet_transfer_prod = post_wallet_transfer_prod
        self.change_order_status_prod = change_order_status_prod

    async def send_order_status(self, order_id: int, user_id, status: str):
        if self.change_order_status_prod:
            message = {"order_id": order_id, "user_id": user_id, "status": status}
            await self.change_order_status_prod.send_order_update(message)
            logger.info(f"📤 SENT ORDER STATUS: {message}")

    async def send_wallet_transfer(self, from_user, to_user, asset, amount):
        if self.post_wallet_transfer_prod:
            transfer = {
                "from_user": from_user,
                "to_user": to_user,
                "asset": asset,
                "amount": amount
            }
            await self.post_wallet_transfer_prod.send_wallet_update(transfer)
            logger.info(f"💸 WALLET TRANSFER: {transfer}")

    cpdef void add_order(self, Order order):
        cdef OrderBook order_book
        cdef str ticker_pair = f"{order.order_ticker}/{order.payment_ticker}"

        if ticker_pair not in self.order_books:
            self.order_books[ticker_pair] = OrderBook(ticker_pair)

        order_book = self.order_books[ticker_pair]
        order_book.add_order(order)
        self.match_orders(order_book)

    cpdef void cancel_order(self, order_id, direction, order_ticker, payment_ticker):
        cdef str ticker_pair = f"{order_ticker}/{payment_ticker}"
        if ticker_pair in self.order_books:
            self.order_books[ticker_pair].remove_order(order_id, direction)

    cdef void match_orders(self, OrderBook order_book):
        cdef Order best_buy
        cdef Order best_sell
        cdef int trade_qty
        cdef int trade_value
        cdef str base_asset
        cdef str quote_asset

        while True:
            best_buy = order_book.get_best_buy()
            best_sell = order_book.get_best_sell()

            if not best_buy or not best_sell or best_buy.price < best_sell.price:
                break

            trade_qty = min(best_buy.qty, best_sell.qty)
            trade_value = trade_qty * best_sell.price
            base_asset = best_buy.order_ticker
            quote_asset = best_buy.payment_ticker

            best_buy.qty -= trade_qty
            best_sell.qty -= trade_qty

            logger.info(f"🔄 TRADE EXECUTED: {trade_qty} {base_asset} @ {best_sell.price} {quote_asset}")

            asyncio.create_task(self.send_wallet_transfer(
                from_user=best_buy.user_id,
                to_user=best_sell.user_id,
                asset=quote_asset,
                amount=trade_value
            ))
            asyncio.create_task(self.send_wallet_transfer(
                from_user=best_sell.user_id,
                to_user=best_buy.user_id,
                asset=base_asset,
                amount=trade_qty
            ))

            if best_buy.qty == 0:
                asyncio.create_task(self.send_order_status(best_buy.order_id, best_buy.user_id, "filled"))
                order_book.remove_order(best_buy.order_id, best_buy.direction)
            else:
                asyncio.create_task(self.send_order_status(best_buy.order_id, best_buy.user_id, "partially_filled"))

            if best_sell.qty == 0:
                asyncio.create_task(self.send_order_status(best_sell.order_id, best_sell.user_id, "filled"))
                order_book.remove_order(best_sell.order_id, best_sell.direction)
            else:
                asyncio.create_task(self.send_order_status(best_sell.order_id, best_sell.user_id, "partially_filled"))

    cdef void execute_market_order(self, Order order):
        cdef OrderBook order_book
        cdef list orders
        cdef Order best_order
        cdef int trade_qty
        cdef int trade_value
        cdef str base_asset
        cdef str quote_asset

        cdef str ticker_pair = f"{order.order_ticker}/{order.payment_ticker}"

        if ticker_pair not in self.order_books:
            logger.warning(f"❌ No order book found for {ticker_pair}. Cancelling market order.")
            asyncio.create_task(self.send_order_status(order.order_id, order.user_id, "cancelled"))
            return

        order_book = self.order_books[ticker_pair]
        orders = order_book.sell_orders if order.direction == "buy" else order_book.buy_orders

        if not orders:
            logger.warning(f"❌ No counter orders in book for market order {order.order_id}. Cancelling.")
            asyncio.create_task(self.send_order_status(order.order_id, order.user_id, "cancelled"))
            return

        while order.qty > 0 and orders:
            best_order = orders[0]

            trade_qty = min(order.qty, best_order.qty)
            trade_value = trade_qty * best_order.price
            base_asset = order.order_ticker
            quote_asset = order.payment_ticker

            order.qty -= trade_qty
            best_order.qty -= trade_qty

            logger.info(
                f"✅ MARKET MATCH: {trade_qty} {base_asset} @ {best_order.price} {quote_asset} "
                f"[order_id={order.order_id} ⇄ {best_order.order_id}]"
            )

            if order.direction == "buy":
                asyncio.create_task(self.send_wallet_transfer(order.user_id, best_order.user_id, quote_asset, trade_value))
                asyncio.create_task(self.send_wallet_transfer(best_order.user_id, order.user_id, base_asset, trade_qty))
            else:
                asyncio.create_task(self.send_wallet_transfer(order.user_id, best_order.user_id, base_asset, trade_qty))
                asyncio.create_task(self.send_wallet_transfer(best_order.user_id, order.user_id, quote_asset, trade_value))

            if order.qty == 0:
                asyncio.create_task(self.send_order_status(order.order_id, order.user_id, "filled"))
            else:
                asyncio.create_task(self.send_order_status(order.order_id, order.user_id, "partially_filled"))

            if best_order.qty == 0:
                asyncio.create_task(self.send_order_status(best_order.order_id, best_order.user_id, "filled"))
                orders.pop(0)
            else:
                asyncio.create_task(self.send_order_status(best_order.order_id, best_order.user_id, "partially_filled"))

        if order.qty > 0:
            logger.warning(f"⚠️ Market order {order.order_id} partially or fully unfilled. Cancelling remainder.")
            asyncio.create_task(self.send_order_status(order.order_id, order.user_id, "cancelled"))
