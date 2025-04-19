import logging
import asyncio
import json
from engine.order cimport Order
from engine.order_book cimport OrderBook
from engine.price_level cimport PriceLevel
from redis_client.redis_client import AsyncRedisOrderClient


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
        object prod_market_quote
        object prod_transaction
        object redis
    
    def __init__(self, change_order_status_prod, post_wallet_transfer_prod, prod_market_quote,
        prod_transaction, redis: AsyncRedisOrderClient):
        self.order_books = {}
        self.post_wallet_transfer_prod = post_wallet_transfer_prod
        self.change_order_status_prod = change_order_status_prod
        self.prod_market_quote = prod_market_quote
        self.prod_transaction = prod_transaction
        self.redis = redis

    async def send_transaction(self, order_asset_id: int, payment_asset_id: int, from_user_id: int, 
                                to_user_id: int, price: int, amount: int):
        
        transaction = {
            "order_asset_id": order_asset_id,
            "payment_asset_id":payment_asset_id,
            "from_user_id": from_user_id,
            "to_user_id":to_user_id,
            "price": price,
            "amount": amount
            }
        
        await self.prod_transaction.send_transaction(transaction)

    async def send_order_status(self, order_id: int, user_id, filled: int, status: str):
        if self.change_order_status_prod:
            message = {"order_id": order_id, "user_id": user_id, "filled": filled, "status": status}
            await self.change_order_status_prod.send_order_update(message)
            logger.info(f"📤 SENT ORDER STATUS: {message}")

    async def send_wallet_transfer(self, from_user, to_user, ticker, amount):
        if self.post_wallet_transfer_prod:
            transfer = {
                "from_user": from_user,
                "to_user": to_user,
                "ticker": ticker,
                "amount": amount
            }
            await self.post_wallet_transfer_prod.send_wallet_update(transfer)
            logger.info(f"💸 WALLET TRANSFER: {transfer}")

    async def update_market_data_in_redis(self, order_book: OrderBook, ticker_pair):
        bid_levels = self.aggregate_orders(order_book.buy_orders, reverse=True)[:5]
        ask_levels = self.aggregate_orders(order_book.sell_orders, reverse=False)[:5]

        bid_levels_dict = self.convert_to_dict(bid_levels)
        ask_levels_dict = self.convert_to_dict(ask_levels)

        await self.redis.set_market_data(ticker_pair, bid_levels_dict, ask_levels_dict)
   
    async def send_market_quote(self, response: dict):
        await self.prod_market_quote.send_market_quote_response(response)

    async def restore_order_books_from_redis(self):
        """Загружает все ордера из Redis в память MatchingEngine."""
        all_books = await self.redis.get_all_order_books()
        for ticker_pair, orders in all_books.items():
            if ticker_pair not in self.order_books:
                self.order_books[ticker_pair] = OrderBook(ticker_pair)
            for field, data in orders.items():
                order = Order(**data)
                self.add_order(order)
        logger.info("✅ Ордербуки успешно восстановлены из Redis.")

    cpdef void handle_market_quote_request(self, correlation_id, order_ticker, payment_ticker, direction, amount):
        cdef OrderBook order_book
        cdef str ticker_pair = f"{order_ticker}/{payment_ticker}"
        cdef dict response = {"correlation_id":correlation_id}
        cdef int available_liquidity
        cdef int required_payment

        if ticker_pair not in self.order_books:
            self.order_books[ticker_pair] = OrderBook(ticker_pair)

        order_book = self.order_books[ticker_pair]

        if direction == "buy":
            available_liquidity = order_book.get_available_sell_liquidity()

            if available_liquidity < amount:
                response["status"] = "error"
                response["reason"] = "insufficient_liquidity"
                response["details"] = f"Available sell liquidity is {available_liquidity}, but requested {amount}."
            else:
                required_payment = order_book.calculate_payment_for_buy(amount)
                response["status"] = "ok"
                response["amount_to_pay"] = required_payment

        elif direction == "sell":
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

        asyncio.create_task(self.send_market_quote(response=response))

    cpdef void add_order(self, Order order):
        cdef OrderBook order_book
        cdef str ticker_pair = f"{order.order_ticker}/{order.payment_ticker}"

        if ticker_pair not in self.order_books:
            self.order_books[ticker_pair] = OrderBook(ticker_pair)

        order_book = self.order_books[ticker_pair]
        order_book.add_order(order)
        
        asyncio.create_task(self.redis.add_order(order))
        asyncio.create_task(self.update_market_data_in_redis(order_book, ticker_pair))
        
        self.match_orders(order_book)

    cpdef void cancel_order(self, order_id, direction, order_ticker, payment_ticker):
        cdef str ticker_pair = f"{order_ticker}/{payment_ticker}"
        cdef OrderBook order_book
        cdef Order order
        cdef int remaining_qty
        cdef int refund_amount

        logger.info(ticker_pair)
        logger.info(self.order_books)
        if ticker_pair not in self.order_books:
            return

        order_book = self.order_books[ticker_pair]
        order = order_book.get_order(order_id, direction)

        if order is None:
            logger.warning(f"❌ Order {order_id} not found for cancellation.")
            return

        remaining_qty = order.qty

        if direction == "buy":
            refund_amount = remaining_qty * order.price
            asyncio.create_task(self.send_wallet_transfer(
                from_user=None,
                to_user=order.user_id,
                ticker=order.payment_ticker,
                amount=refund_amount
            ))
        else:
            asyncio.create_task(self.send_wallet_transfer(
                from_user=None,
                to_user=order.user_id,
                ticker=order.order_ticker,
                amount=remaining_qty
            ))

        order_book.remove_order(order_id, direction)
        
        asyncio.create_task(self.redis.remove_order(order_id, ticker_pair, direction))
        asyncio.create_task(self.update_market_data_in_redis(order_book, ticker_pair))

        logger.info(f"🚫 CANCELLED ORDER {order_id}, returned unspent: {remaining_qty} ({'qty' if direction == 'sell' else 'value'})")

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

            best_buy.qty -= trade_qty
            best_sell.qty -= trade_qty

            best_buy.filled += trade_qty
            best_sell.filled += trade_qty

            logger.info(f"🔄 TRADE EXECUTED: {trade_qty} {best_buy.order_ticker} @ {best_sell.price} {best_buy.payment_ticker}")

            asyncio.create_task(self.send_wallet_transfer(
                from_user=best_buy.user_id,
                to_user=best_sell.user_id,
                ticker=best_buy.payment_ticker,
                amount=trade_value
            ))
            asyncio.create_task(self.send_wallet_transfer(
                from_user=best_sell.user_id,
                to_user=best_buy.user_id,
                ticker=best_buy.order_ticker,
                amount=trade_qty
            ))

            asyncio.create_task(self.send_transaction(
                order_asset_id=best_buy.order_asset_id,
                payment_asset_id=best_sell.payment_asset_id,
                from_user_id=best_buy.user_id,
                to_user_id=best_sell.user_id,
                price=best_sell.price,
                amount=trade_qty,
            ))

            if best_buy.qty == 0:
                asyncio.create_task(self.send_order_status(best_buy.order_id, best_buy.user_id, best_buy.filled, "filled"))
                
                order_book.remove_order(best_buy.order_id, best_buy.direction)
                asyncio.create_task(self.redis.remove_order(best_buy.order_id, ticker_pair, best_buy.direction))
            else:
                asyncio.create_task(self.send_order_status(best_buy.order_id, best_buy.user_id, best_buy.filled, "partially_filled"))

            if best_sell.qty == 0:
                asyncio.create_task(self.send_order_status(best_sell.order_id, best_sell.user_id, best_sell.filled, "filled"))
                
                order_book.remove_order(best_sell.order_id, best_sell.direction)
                asyncio.create_task(self.redis.remove_order(best_sell.order_id, ticker_pair, best_sell.direction))
            else:
                asyncio.create_task(self.send_order_status(best_sell.order_id, best_sell.user_id, best_sell.filled, "partially_filled"))

        if traded:
            asyncio.create_task(self.update_market_data_in_redis(order_book, ticker_pair))

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
            asyncio.create_task(self.send_order_status(order.order_id, order.user_id, 0, "cancelled"))
            return

        order_book = self.order_books[ticker_pair]
        orders = order_book.sell_orders if order.direction == "buy" else order_book.buy_orders

        if not orders:
            logger.warning(f"❌ No counter orders in book for market order {order.order_id}. Cancelling.")
            asyncio.create_task(self.send_order_status(order.order_id, order.user_id, 0, "cancelled"))
            return

        # 🔍 Dry-run: проверяем, хватит ли объёма
        for o in orders:
            available_qty += o.qty
            if available_qty >= order.qty:
                break

        if available_qty < order.qty:
            logger.warning(f"⚠️ Not enough liquidity to fill market order {order.order_id}. Cancelling.")
            asyncio.create_task(self.send_order_status(order.order_id, order.user_id, 0, "cancelled"))
            return

        # ✅ Полное исполнение — ликвидность есть
        base_asset_ticker = order.order_ticker
        quote_asset_ticker = order.payment_ticker

        while order.qty > 0 and orders:
            best_order = orders[0]
            trade_qty = min(order.qty, best_order.qty)
            trade_value = trade_qty * best_order.price

            order.qty -= trade_qty
            best_order.qty -= trade_qty

            order.filled += trade_qty
            best_order.filled += trade_qty

            logger.info(
                f"✅ MARKET MATCH: {trade_qty} {base_asset_ticker} @ {best_order.price} {quote_asset_ticker} "
                f"[order_id={order.order_id} ⇄ {best_order.order_id}]"
            )

            if order.direction == "buy":
                asyncio.create_task(self.send_wallet_transfer(order.user_id, best_order.user_id, quote_asset_ticker, trade_value))
                asyncio.create_task(self.send_wallet_transfer(best_order.user_id, order.user_id, base_asset_ticker, trade_qty))

                asyncio.create_task(self.send_transaction(
                    from_user_id=order.user_id,
                    to_user_id=best_order.user_id,
                    order_asset_id=order.order_asset_id,
                    payment_asset_id=best_order.payment_asset_id,
                    price=best_order.price,
                    amount=trade_qty
                ))

            else:
                asyncio.create_task(self.send_wallet_transfer(order.user_id, best_order.user_id, base_asset_ticker, trade_qty))
                asyncio.create_task(self.send_wallet_transfer(best_order.user_id, order.user_id, quote_asset_ticker, trade_value))

                asyncio.create_task(self.send_transaction(
                    from_user_id=order.user_id,
                    to_user_id=best_order.user_id,
                    order_asset_id=order.order_asset_id,
                    payment_asset_id=best_order.payment_asset_id,
                    price=best_order.price,
                    amount=trade_value
                ))

            if best_order.qty == 0:
                asyncio.create_task(self.send_order_status(best_order.order_id, best_order.user_id, best_order.filled, "filled"))
                
                orders.pop(0)
                asyncio.create_task(self.redis.remove_order(best_order.order_id, ticker_pair, best_order.direction))
                
            else:
                asyncio.create_task(self.send_order_status(best_order.order_id, best_order.user_id, best_order.filled, "partially_filled"))

        asyncio.create_task(self.send_order_status(order.order_id, order.user_id, order.filled, "filled"))
        asyncio.create_task(self.update_market_data_in_redis(order_book, ticker_pair))
    
    cdef list aggregate_orders(self, list orders, bint reverse=True):
        cdef dict price_to_qty = {}
        cdef list prices = []
        cdef list result = []
        cdef Order order
        cdef PriceLevel level
        cdef int price

        # Агрегируем ордера по цене
        for order in orders:
            price = order.price
            if price in price_to_qty:
                price_to_qty[price] += order.qty
            else:
                price_to_qty[price] = order.qty
                prices.append(price)

        # Сортируем по цене
        prices.sort(reverse=reverse)

        # Наполняем список PriceLevel
        for price in prices:
            level = PriceLevel(price=price, qty=price_to_qty[price])
            result.append(level)

        return result

    cdef list convert_to_dict(self, list price_levels):
        cdef list result = []
        cdef PriceLevel level

        for level in price_levels:
            result.append({"price": level.price, "qty": level.qty})

        return result
