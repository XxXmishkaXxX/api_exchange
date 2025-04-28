from fastapi import APIRouter, Depends
from uuid import UUID
from typing import Annotated

from app.deps.services import get_order_service
from app.schemas.order import (OrderSchema, 
                               OrderCreateResponse, 
                               OrderListResponse, 
                               OrderResponse, 
                               OrderCancelResponse)
from app.deps.security import get_user_from_token
from app.services.order import OrderService

router = APIRouter()


@router.get("/{order_id}", response_model=OrderResponse | None)
async def get_order(
    order_id: UUID,
    user_id: Annotated[UUID, Depends(get_user_from_token)],
    service: Annotated[OrderService, Depends(get_order_service)]
) -> OrderResponse:
    """
    Получить информацию о заказе по ID.

    Аргументы:
        order_id (UUID): ID заказа.
        user_id (UUID): Данные пользователя, полученные через верификацию токена.
        service (OrderService): Сервис для работы с заказами.

    Возвращает:
        OrderResponse: Ответ с информацией о заказе.
    """
    return await service.get_order(user_id, order_id)


@router.get("/", response_model=OrderListResponse | None)
async def get_orders_list(
    user_id: Annotated[UUID, Depends(get_user_from_token)],
    service: Annotated[OrderService, Depends(get_order_service)]
) -> OrderListResponse:
    """
    Получить список заказов пользователя.

    Аргументы:
        user_id (UUID): Данные пользователя, полученные через верификацию токена.
        service (OrderService): Сервис для работы с заказами.

    Возвращает:
        OrderListResponse: Ответ с списком заказов пользователя.
    """
    return await service.get_list_order(user_id)


@router.post("/", response_model=OrderCreateResponse)
async def create_order(
    order: OrderSchema,
    user_id: Annotated[UUID, Depends(get_user_from_token)],
    service: Annotated[OrderService, Depends(get_order_service)]
) -> OrderCreateResponse:
    """
    Создать новый заказ.

    Аргументы:
        order (OrderSchema): Данные для создания нового заказа.
        user_id (UUID): Данные пользователя, полученные через верификацию токена.
        service (OrderService): Сервис для работы с заказами.

    Возвращает:
        OrderCreateResponse: Ответ с информацией о созданном заказе.
    """
    return await service.create_order(user_id, order)


@router.delete("/{order_id}", response_model=OrderCancelResponse)
async def cancel_order(
    order_id: UUID,
    user_id: Annotated[UUID, Depends(get_user_from_token)],
    service: Annotated[OrderService, Depends(get_order_service)]
) -> OrderCancelResponse:
    """
    Отменить заказ по ID.

    Аргументы:
        order_id (UUID): ID заказа для отмены.
        user_id (UUID): Данные пользователя, полученные через верификацию токена.
        service (OrderService): Сервис для работы с заказами.

    Возвращает:
        OrderCancelResponse: Ответ с информацией об успешной отмене заказа.
    """
    return await service.cancel_order(user_id, order_id)

