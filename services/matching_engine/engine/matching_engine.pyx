import asyncio
import time
import json
from core.loggers.system_logger import logger
from core.loggers.orders_action_logger import logger as orders_action_logger
from messaging.producer_service import ProducerService
from engine.order cimport Order
from engine.order_book cimport OrderBook
from engine.price_level cimport PriceLevel
from redis_client.redis_client import RedisOrderClient



cdef class MatchingEngine:
    cdef:
        object messaging
        object redis
        public dict order_books

    def __init__(self, order_books: dict, messaging_service: ProducerService, redis: RedisOrderClient):
        logger.info(order_books)
        self.order_books = order_books
        self.messaging = messaging_service
        self.redis = redis

    def update_market_data_in_redis(self, order_book: OrderBook, ticker_pair):
        bid_levels = order_book.get_price_levels("BUY")
        ask_levels = order_book.get_price_levels("SELL")

        bid_levels_dict = self.convert_to_dict(bid_levels)
        ask_levels_dict = self.convert_to_dict(ask_levels)

        # ✅ Обновление Redis
        self.redis.set_market_data(ticker_pair, bid_levels_dict, ask_levels_dict)

        # 🪵 Логируем стакан
        log_lines = []
        log_lines.append("\n  🟥 ASK (Sell Orders)        🟩 BID (Buy Orders)")
        for ask, bid in zip(ask_levels, bid_levels):
            ask_str = f"{ask['price']:<8} | {ask['qty']:<6}"
            bid_str = f"{bid['price']:<8} | {bid['qty']:<6}"
            log_lines.append(f"  {ask_str}        {bid_str}")

            logger.info("\n".join(log_lines))
        

    cpdef void handle_market_quote_request(self, correlation_id, order_ticker, payment_ticker, direction, amount):
        cdef OrderBook order_book
        cdef str ticker_pair = f"{order_ticker}/{payment_ticker}"
        cdef dict response = {"correlation_id":correlation_id}
        cdef int available_liquidity
        cdef int required_payment

        if ticker_pair not in self.order_books:
            self.order_books[ticker_pair] = OrderBook(ticker_pair)

        order_book = self.order_books[ticker_pair]

        if direction == "BUY":
            available_liquidity = order_book.get_available_sell_liquidity()

            if available_liquidity < amount:
                response["status"] = "error"
                response["reason"] = "insufficient_liquidity"
                response["details"] = f"Available sell liquidity is {available_liquidity}, but requested {amount}."
            else:
                required_payment = order_book.calculate_payment_for_buy(amount)
                response["status"] = "ok"
                response["amount_to_pay"] = required_payment

        elif direction == "SELL":
            available_liquidity = order_book.get_available_buy_liquidity()

            if available_liquidity < amount:
                response["status"] = "error"
                response["reason"] = "insufficient_liquidity"
                response["details"] = f"Available buy liquidity is {available_liquidity}, but requested {amount}."
            else:
                response["status"] = "ok"
                response["liquidity"] = available_liquidity

        else:
            response["status"] = "error"
            response["reason"] = "invalid_direction"
            response["details"] = "Direction must be 'buy' or 'sell'."

        asyncio.create_task(self.messaging.send_market_quote(response=response))

    cpdef void add_order(self, Order order):
        cdef OrderBook order_book
        cdef str ticker_pair = f"{order.order_ticker}/{order.payment_ticker}"

        if ticker_pair not in self.order_books:
            self.order_books[ticker_pair] = OrderBook(ticker_pair)

        order_book = self.order_books[ticker_pair]
        order_book.add_order(order)
        orders_action_logger.info(json.dumps({
                                    "timestamp": int(time.time()),
                                    "action": "add",
                                    "order": order.to_dict(),
                                }))
        self.update_market_data_in_redis(order_book, ticker_pair)
        
        self.match_orders(order_book)

    cpdef void cancel_order(self, order_id, direction, order_ticker, payment_ticker):
        cdef str ticker_pair = f"{order_ticker}/{payment_ticker}"
        cdef OrderBook order_book
        cdef Order order
        cdef int remaining_qty
        cdef int refund_amount

        if ticker_pair not in self.order_books:
            return

        order_book = self.order_books[ticker_pair]
        order = order_book.get_order(order_id, direction)

        if order is None:
            logger.warning(f"❌ Order {order_id} not found for cancellation.")
            return

        remaining_qty = order.qty

        if direction == "BUY":
            refund_amount = remaining_qty * order.price
            asyncio.create_task(self.messaging.send_wallet_transfer(
                from_user=None,
                to_user=order.user_id,
                asset_id=order.payment_asset_id,
                amount=refund_amount
            ))
        else:
            asyncio.create_task(self.messaging.send_wallet_transfer(
                from_user=None,
                to_user=order.user_id,
                asset_id=order.order_asset_id,
                amount=remaining_qty
            ))

        order_book.remove_order(order_id, direction)

        orders_action_logger.info(json.dumps({
                                    "timestamp": int(time.time()),
                                    "action": "remove",
                                    "order_id": order_id,
                                    "direction": direction
                                }))
        
        self.update_market_data_in_redis(order_book, ticker_pair)
        asyncio.create_task(self.messaging.send_order_status(order.order_id, order.user_id, order.filled, status="CANCELLED"))

        logger.info(f"🚫 CANCELLED ORDER {order_id}, returned unspent: {remaining_qty} ({'qty' if direction == 'SELL' else 'value'})")

    cdef void match_orders(self, OrderBook order_book):
        cdef Order best_buy
        cdef Order best_sell
        cdef int trade_qty
        cdef int trade_value
        cdef bint traded = False
        cdef str ticker_pair = order_book.ticker_pair_name

        while True:
            best_buy = order_book.get_best_buy()
            best_sell = order_book.get_best_sell()

            if not best_buy or not best_sell or best_buy.price < best_sell.price:
                break

            traded = True
            trade_qty = min(best_buy.qty, best_sell.qty)
            trade_value = trade_qty * best_sell.price

            order_book.decrease_order_qty(best_buy, trade_qty)
            order_book.decrease_order_qty(best_sell, trade_qty)


            best_buy.filled += trade_qty
            best_sell.filled += trade_qty

            logger.info(f"🔄 TRADE EXECUTED: {trade_qty} {best_buy.order_ticker} @ {best_sell.price} {best_buy.payment_ticker}")

            asyncio.create_task(self.messaging.send_wallet_transfer(
                from_user=best_buy.user_id,
                to_user=best_sell.user_id,
                asset_id=best_buy.payment_asset_id,
                amount=trade_value
            ))
            asyncio.create_task(self.messaging.send_wallet_transfer(
                from_user=best_sell.user_id,
                to_user=best_buy.user_id,
                asset_id=best_buy.order_asset_id,
                amount=trade_qty
            ))

            asyncio.create_task(self.messaging.send_transaction(
                order_ticker=best_buy.order_ticker,
                payment_ticker=best_sell.payment_ticker,
                from_user_id=best_buy.user_id,
                to_user_id=best_sell.user_id,
                price=best_sell.price,
                amount=trade_qty,
            ))

            if best_buy.qty == 0:
                asyncio.create_task(self.messaging.send_order_status(best_buy.order_id, best_buy.user_id, best_buy.filled, "EXECUTED"))
                
                order_book.remove_order(best_buy.order_id, best_buy.direction)
                orders_action_logger.info(json.dumps({
                                    "timestamp": int(time.time()),
                                    "action": "remove",
                                    "order_id": best_buy.order_id,
                                    "direction": best_buy.direction
                                }))
            else:
                asyncio.create_task(self.messaging.send_order_status(best_buy.order_id, best_buy.user_id, best_buy.filled, "PARTIALLY_EXECUTED"))
                orders_action_logger.info(json.dumps({
                                    "timestamp": int(time.time()),
                                    "action": "update",
                                    "order_id": best_buy.to_dict(),
                                }))
            if best_sell.qty == 0:
                asyncio.create_task(self.messaging.send_order_status(best_sell.order_id, best_sell.user_id, best_sell.filled, "EXECUTED"))
                
                order_book.remove_order(best_sell.order_id, best_sell.direction)
                orders_action_logger.info(json.dumps({
                                    "timestamp": int(time.time()),
                                    "action": "remove",
                                    "order_id": best_sell.order_id,
                                    "direction": best_sell.direction
                                }))
            else:
                asyncio.create_task(self.messaging.send_order_status(best_sell.order_id, best_sell.user_id, best_sell.filled, "PARTIALLY_EXECUTED"))
                orders_action_logger.info(json.dumps({
                                    "timestamp": int(time.time()),
                                    "action": "update",
                                    "order_id": best_sell.to_dict(),
                                }))
        if traded:
            self.update_market_data_in_redis(order_book, ticker_pair)

    cpdef void execute_market_order(self, Order order):
        cdef OrderBook order_book
        cdef list orders
        cdef Order best_order
        cdef int trade_qty
        cdef int trade_value
        cdef str ticker_pair = f"{order.order_ticker}/{order.payment_ticker}"
        cdef int remaining_qty = order.qty
        cdef int available_qty = 0

        if ticker_pair not in self.order_books:
            logger.warning(f"❌ No order book found for {ticker_pair}. Cancelling market order.")
            asyncio.create_task(self.messaging.send_order_status(order.order_id, order.user_id, 0, "CANCELLED"))
            return

        order_book = self.order_books[ticker_pair]
        orders = order_book.sell_orders if order.direction == "BUY" else order_book.buy_orders

        if not orders:
            logger.warning(f"❌ No counter orders in book for market order {order.order_id}. Cancelling.")
            asyncio.create_task(self.messaging.send_order_status(order.order_id, order.user_id, 0, "CANCELLED"))
            return

        # 🔍 Dry-run: проверяем, хватит ли объёма
        for o in orders:
            available_qty += o.qty
            if available_qty >= order.qty:
                break

        if available_qty < order.qty:
            logger.warning(f"⚠️ Not enough liquidity to fill market order {order.order_id}. Cancelling.")
            asyncio.create_task(self.messaging.send_order_status(order.order_id, order.user_id, 0, "CANCELLED"))
            return

        # ✅ Полное исполнение — ликвидность есть
        base_asset_ticker = order.order_asset_id
        quote_asset_ticker = order.payment_asset_id

        while order.qty > 0 and orders:
            best_order = orders[0]
            trade_qty = min(order.qty, best_order.qty)
            trade_value = trade_qty * best_order.price

            order.qty -= trade_qty
            order_book.decrease_order_qty(best_order, trade_qty)

            order.filled += trade_qty
            best_order.filled += trade_qty

            logger.info(
                f"✅ MARKET MATCH: {trade_qty} {base_asset_ticker} @ {best_order.price} {quote_asset_ticker} "
                f"[order_id={order.order_id} ⇄ {best_order.order_id}]"
            )

            if order.direction == "BUY":
                asyncio.create_task(self.messaging.send_wallet_transfer(order.user_id, best_order.user_id, quote_asset_ticker, trade_value))
                asyncio.create_task(self.messaging.send_wallet_transfer(best_order.user_id, order.user_id, base_asset_ticker, trade_qty))

                asyncio.create_task(self.messaging.send_transaction(
                    from_user_id=order.user_id,
                    to_user_id=best_order.user_id,
                    order_ticker=order.order_ticker,
                    payment_ticker=best_order.payment_ticker,
                    price=best_order.price,
                    amount=trade_qty
                ))

            else:
                asyncio.create_task(self.messaging.send_wallet_transfer(order.user_id, best_order.user_id, base_asset_ticker, trade_qty))
                asyncio.create_task(self.messaging.send_wallet_transfer(best_order.user_id, order.user_id, quote_asset_ticker, trade_value))

                asyncio.create_task(self.messaging.send_transaction(
                    from_user_id=order.user_id,
                    to_user_id=best_order.user_id,
                    order_ticker=order.order_ticker,
                    payment_ticker=best_order.payment_ticker,
                    price=best_order.price,
                    amount=trade_value
                ))

            if best_order.qty == 0:
                asyncio.create_task(self.messaging.send_order_status(best_order.order_id, best_order.user_id, best_order.filled, "EXECUTED"))
                
                orders.pop(0)
                orders_action_logger.info(json.dumps({
                                    "timestamp": int(time.time()),
                                    "action": "remove",
                                    "order_id": best_order.order_id,
                                    "direction": best_order.direction
                                }))
                
            else:
                asyncio.create_task(self.messaging.send_order_status(best_order.order_id, best_order.user_id, best_order.filled, "PARTIALLY_EXECUTED"))
                orders_action_logger.info(json.dumps({
                                    "timestamp": int(time.time()),
                                    "action": "update",
                                    "order_id": best_order.to_dict(),
                                }))
        self.update_market_data_in_redis(order_book, ticker_pair)
        asyncio.create_task(self.messaging.send_order_status(order.order_id, order.user_id, order.filled, "EXECUTED"))

    cdef list convert_to_dict(self, list price_levels):
        cdef list result = []
        cdef PriceLevel level

        for level in price_levels:
            result.append({"price": level.price, "qty": level.qty})

        return result
