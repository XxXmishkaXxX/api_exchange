from pydantic import BaseModel, RootModel, Field, ConfigDict, field_validator
from typing import Optional, List, Annotated
from enum import Enum
from uuid import UUID
from datetime import datetime

class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class StatusOrder(str, Enum):
    NEW = "NEW"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"

class OrderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    direction: Annotated[Direction, Field(description="Направление ордера: 'buy' или 'sell'")]
    ticker: Annotated[str, Field(description="Тикер актива для покупки/продажи")]
    payment_ticker: Annotated[Optional[str], Field(default="RUB", description="Тикер актива для расчета (по умолчанию 'RUB')")]
    qty: Annotated[int, Field(gt=0, description="Количество должно быть положительным числом")]
    price: Annotated[Optional[int], Field(default=None, gt=0, description="Цена для лимитного ордера (должна быть положительной)")]

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

class LimitOrderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    direction: Annotated[Direction, Field(description="Направление ордера: 'BUY' или 'SELL'")]
    ticker: Annotated[str, Field(description="Тикер актива для покупки/продажи")]
    qty: Annotated[int, Field(gt=0, description="Количество должно быть положительным числом")]
    price: Annotated[Optional[int], Field(default=None, gt=0, description="Цена для лимитного ордера (должна быть положительной)")]


class MarketOrderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    direction: Annotated[Direction, Field(description="Направление ордера: 'BUY' или 'SELL'")]
    ticker: Annotated[str, Field(description="Тикер актива для покупки/продажи")]
    qty: Annotated[int, Field(gt=0, description="Количество должно быть положительным числом")]



class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True, json_encoders={}, exclude_none=True  # можно оставить как есть
                              )

    id: Annotated[UUID, Field(description="id ордера")]
    user_id: Annotated[UUID, Field(description="id пользователя")]
    status: Annotated[StatusOrder, Field(description="Статус ордера")]
    timestamp: Annotated[datetime, Field(description="Дата и время создания ордера в формате ISO 8601")]
    body: LimitOrderSchema | MarketOrderSchema
    filled: Annotated[int, Field(description="Количество ордера, которое было выполнено.")]

class LimitOrderResponse(OrderResponse):
    filled: Annotated[int, Field(description="Количество ордера, которое было выполнено.")]

class MarketOrderResponse(OrderResponse):
    pass

class OrderListResponse(RootModel[List[LimitOrderResponse | MarketOrderResponse| OrderResponse]]):
    pass
