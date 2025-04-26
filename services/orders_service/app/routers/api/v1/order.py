from fastapi import APIRouter, Depends
from uuid import UUID

from app.deps.services import get_order_service
from app.schemas.order import OrderSchema, OrderCreateResponse, OrderListResponse, OrderResponse, OrderCancelResponse
from app.deps.security import get_user_from_token
from app.services.order import OrderService
from app.services.producers import (get_lock_assets_producer, 
                                   get_order_producer_service,
                                   get_market_qoute_producer, 
                                   OrderKafkaProducerService, 
                                   LockAssetsKafkaProducerService,
                                   MarketQuoteKafkaProducerService)

router = APIRouter()


@router.get("/", response_model=OrderListResponse | None)
async def get_orders_list(
    user_data: dict = Depends(get_user_from_token),
    service: OrderService = Depends(get_order_service)
) -> OrderListResponse:
    """
    Получить список заказов пользователя.

    Аргументы:
        user_data (dict): Данные пользователя, полученные через верификацию токена.
        service (OrderService): Сервис для работы с заказами.

    Возвращает:
        OrderListResponse: Ответ с списком заказов пользователя.
    """
    return await service.get_list_order(user_data)


@router.post("/", response_model=OrderCreateResponse)
async def create_order(
    order: OrderSchema,
    user_data: dict = Depends(get_user_from_token),
    service: OrderService = Depends(get_order_service),
    prod_order: OrderKafkaProducerService = Depends(get_order_producer_service),
    prod_lock: LockAssetsKafkaProducerService = Depends(get_lock_assets_producer),
    prod_market_quote: MarketQuoteKafkaProducerService = Depends(get_market_qoute_producer) 
) -> OrderCreateResponse:
    """
    Создать новый заказ.

    Аргументы:
        order (OrderSchema): Данные для создания нового заказа.
        user_data (dict): Данные пользователя, полученные через верификацию токена.
        service (OrderService): Сервис для работы с заказами.
        prod (KafkaProducerService): Сервис для отправки сообщений в Kafka.

    Возвращает:
        OrderCreateResponse: Ответ с информацией о созданном заказе.
    """
    return await service.create_order(user_data, order, prod_order=prod_order, prod_lock=prod_lock, prod_get_market_quote=prod_market_quote)


@router.get("/{order_id}", response_model=OrderResponse | None)
async def get_order(
    order_id: UUID,
    user_data: dict = Depends(get_user_from_token),
    service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """
    Получить информацию о заказе по ID.

    Аргументы:
        order_id (UUID): ID заказа.
        user_data (dict): Данные пользователя, полученные через верификацию токена.
        service (OrderService): Сервис для работы с заказами.

    Возвращает:
        OrderResponse: Ответ с информацией о заказе.
    """
    return await service.get_order(user_data, order_id)


@router.delete("/{order_id}", response_model=OrderCancelResponse)
async def cancel_order(
    order_id: UUID,
    user_data: dict = Depends(get_user_from_token),
    service: OrderService = Depends(get_order_service),
    prod_order: OrderKafkaProducerService = Depends(get_order_producer_service)
) -> OrderCancelResponse:
    """
    Отменить заказ по ID.

    Аргументы:
        order_id (UUID): ID заказа для отмены.
        user_data (dict): Данные пользователя, полученные через верификацию токена.
        service (OrderService): Сервис для работы с заказами.
        prod (KafkaProducerService): Сервис для отправки сообщений в Kafka.

    Возвращает:
        OrderCancelResponse: Ответ с информацией об успешной отмене заказа.
    """
    return await service.cancel_order(user_data, order_id, prod_order=prod_order)
