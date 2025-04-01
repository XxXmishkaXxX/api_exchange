from fastapi import APIRouter, Depends

from app.schemas.order import OrderSchema, OrderCreateResponse, OrderListResponse, OrderResponse, OrderCancelResponse
from app.deps.security import get_user_from_token
from app.services.order import OrderService, get_order_service
from app.services.producer import get_producer_service, KafkaProducerService

router = APIRouter()


@router.get("/", response_model=OrderListResponse)
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
    prod: KafkaProducerService = Depends(get_producer_service)
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
    return await service.create_order(user_data, order, prod)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    user_data: dict = Depends(get_user_from_token),
    service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """
    Получить информацию о заказе по ID.

    Аргументы:
        order_id (int): ID заказа.
        user_data (dict): Данные пользователя, полученные через верификацию токена.
        service (OrderService): Сервис для работы с заказами.

    Возвращает:
        OrderResponse: Ответ с информацией о заказе.
    """
    return await service.get_order(user_data, order_id)


@router.delete("/{order_id}", response_model=OrderCancelResponse)
async def cancel_order(
    order_id: int,
    user_data: dict = Depends(get_user_from_token),
    service: OrderService = Depends(get_order_service),
    prod: KafkaProducerService = Depends(get_producer_service)
) -> OrderCancelResponse:
    """
    Отменить заказ по ID.

    Аргументы:
        order_id (int): ID заказа для отмены.
        user_data (dict): Данные пользователя, полученные через верификацию токена.
        service (OrderService): Сервис для работы с заказами.
        prod (KafkaProducerService): Сервис для отправки сообщений в Kafka.

    Возвращает:
        OrderCancelResponse: Ответ с информацией об успешной отмене заказа.
    """
    return await service.cancel_order(user_data, order_id, prod)
