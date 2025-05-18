from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Annotated
from enum import Enum
from uuid import UUID
from datetime import datetime

class Direction(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"

class StatusOrder(str, Enum):
    NEW = "NEW"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"

class OrderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: Annotated[OrderType, Field(description="Тип ордера: 'market' или 'limit'")]
    direction: Annotated[Direction, Field(description="Направление ордера: 'buy' или 'sell'")]
    ticker: Annotated[str, Field(description="Тикер актива для покупки/продажи")]
    payment_ticker: Annotated[Optional[str], Field(default="RUB", description="Тикер актива для расчета (по умолчанию 'RUB')")]
    qty: Annotated[int, Field(gt=0, description="Количество должно быть положительным числом")]
    price: Annotated[Optional[int], Field(default=None, gt=0, description="Цена для лимитного ордера (должна быть положительной)")]

    @field_validator("price", mode="before")
    @classmethod
    def price_required_for_limit_orders(cls, value, info):
        if info.data.get("type") == OrderType.LIMIT and value is None:
            raise ValueError("Цена обязательна для лимитных ордеров")
        return value

    @field_validator("payment_ticker", mode="before")
    @classmethod
    def default_payment_ticker(cls, value):
        return value or "RUB"

    @field_validator("payment_ticker")
    @classmethod
    def tickers_must_be_different(cls, payment_ticker, info):
        ticker = info.data.get("ticker")
        if ticker and payment_ticker and ticker == payment_ticker:
            raise ValueError("Тикер актива и тикер для расчета не могут совпадать")
        return payment_ticker

class OrderCreateResponse(BaseModel):
    success: Annotated[bool, Field(description="Успешность выполнения заявки")]
    order_id: Annotated[UUID, Field(description="Уникальный идентификатор заявки")]

class OrderCancelResponse(BaseModel):
    success: Annotated[bool, Field(description="Успешность отмены заявки")]

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: Annotated[UUID, Field(description="id ордера")]
    user_id: Annotated[UUID, Field(description="id пользователя")]
    status: Annotated[StatusOrder, Field(description="Статус ордера")]
    timestamp: Annotated[datetime, Field(description="Дата и время создания ордера в формате ISO 8601")]
    body: OrderSchema
    filled: Annotated[int, Field(description="Количество ордера, которое было выполнено.")]

class OrderListResponse(BaseModel):
    orders: Annotated[List[OrderResponse], Field(description="Список ордеров пользователя")]
