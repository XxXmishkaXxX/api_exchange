import json

from app.kafka.consumers.base_consumer import BaseKafkaConsumerService
from app.services.response_listeners import market_quote_futures
from app.core.config import settings

class MarketQuoteResponseKafkaConsumerServcie(BaseKafkaConsumerService):
    async def process_message(self, message):
        try:
            value = json.loads(message.value.decode("utf-8"))
            correlation_id = value.get("correlation_id")
            status = value.get("status", "error")

            await self.log_message("Получен маркет-респонс", correlation_id=correlation_id, status=status)

            if correlation_id and correlation_id in market_quote_futures:
                    future = market_quote_futures.pop(correlation_id)
                    future.set_result(value)

        except Exception as e:
            await self.log_message("Ошибка обработки маркет-респонса", error=str(e))

market_quote_response_consumer = MarketQuoteResponseKafkaConsumerServcie(
    settings.MARKET_QUOTE_RESPONSE_TOPIC, settings.BOOTSTRAP_SERVERS, group_id="market_quote_group"
)
