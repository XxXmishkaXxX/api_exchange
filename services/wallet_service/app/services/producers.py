import json
from aiokafka import AIOKafkaProducer
from typing import AsyncGenerator

from app.core.config import settings


class BaseKafkaProducerService:
    """
    Сервис для взаимодействия с Kafka, отправляющий сообщения о заказах.
    
    Этот сервис позволяет отправлять информацию о новых и отменённых ордерах в Kafka.
    """

    def __init__(self, bootstrap_servers: str):
        """
        Инициализация Kafka продюсера.

        Аргументы:
            bootstrap_servers (str): Адреса серверов Kafka.
        """
        self.bootstrap_servers = bootstrap_servers
        self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)

    async def start(self) -> None:
        """Запуск продюсера Kafka."""
        await self.producer.start()

    async def stop(self) -> None:
        """Остановка продюсера Kafka."""
        await self.producer.stop()

    async def send_message(self, data: dict):

        raise NotImplementedError("Метод process_message должен быть реализован в наследниках")
    
    
class ChangeBalanceKafkaProducerService(BaseKafkaProducerService):

    def __init__(self, bootstrap_servers: str):
        super().__init__(bootstrap_servers=bootstrap_servers)
    
    async def send_message(self, data: dict):
        
        await self.producer.send_and_wait("change_balance", data)


change_balance_producer_service = ChangeBalanceKafkaProducerService(bootstrap_servers=settings.BOOTSTRAP_SERVERS)



async def get_change_balance_producer_service() -> AsyncGenerator[ChangeBalanceKafkaProducerService, None]:
    """
    Асинхронный генератор для получения экземпляра сервиса Kafka продюсера.

    Возвращает:
        ChangeBalanceKafkaProducerService: Экземпляр сервиса Kafka продюсера.
    """
    yield change_balance_producer_service
