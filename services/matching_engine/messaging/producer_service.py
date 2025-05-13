from core.loggers.system_logger import logger

class ProducerService:
    def __init__(self, change_order_status_prod, post_wallet_transfer_prod, 
                 prod_market_quote, prod_transaction):
        self.change_order_status_prod = change_order_status_prod
        self.post_wallet_transfer_prod = post_wallet_transfer_prod
        self.prod_market_quote = prod_market_quote
        self.prod_transaction = prod_transaction

    async def send_transaction(self, order_asset_id, payment_asset_id, from_user_id, to_user_id, price, amount):
        transaction = {
            "order_asset_id": order_asset_id,
            "payment_asset_id": payment_asset_id,
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "price": price,
            "amount": amount,
        }
        await self.prod_transaction.send_transaction(transaction)

    async def send_order_status(self, order_id, user_id, filled, status):
        if self.change_order_status_prod:
            message = {"order_id": order_id, "user_id": user_id, "filled": filled, "status": status}
            await self.change_order_status_prod.send_order_update(message)
            logger.info(f"📤 SENT ORDER STATUS: {message}")

    async def send_wallet_transfer(self, from_user, to_user, asset_id, amount):
        if self.post_wallet_transfer_prod:
            transfer = {
                "from_user": from_user,
                "to_user": to_user,
                "asset_id": asset_id,
                "amount": amount
            }
            await self.post_wallet_transfer_prod.send_wallet_update(transfer)
            logger.info(f"💸 WALLET TRANSFER: {transfer}")

    async def send_market_quote(self, response: dict):
        await self.prod_market_quote.send_market_quote_response(response)
