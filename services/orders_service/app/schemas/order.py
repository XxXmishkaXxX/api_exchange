from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum

# Перечисление для направления ордера
class Direction(str, Enum):
    BUY = "buy"
    SELL = "sell"

# Перечисление для типа ордера
class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"

# Базовая модель ордера
class Order(BaseModel):
    type: OrderType = Field(description="Тип ордера: 'market' или 'limit'")
    direction: Direction = Field(description="Направление ордера: 'buy' или 'sell'")
    ticker: str = Field(min_length=1, max_length=10, description="Тикер актива (например, 'AAPL')")
    qty: int = Field(gt=0, description="Количество должно быть положительным числом")
    price: Optional[float] = Field(None, gt=0, description="Цена для лимитного ордера (должна быть положительной)")

    @validator("ticker")
    def ticker_must_be_uppercase(cls, value):
        if not value.isupper():
            raise ValueError("Тикер должен быть в верхнем регистре")
        return value

    @validator("price")
    def price_required_for_limit_orders(cls, value, values):
        if values["type"] == OrderType.LIMIT and value is None:
            raise ValueError("Цена обязательна для лимитных ордеров")
        return value

class OrderResponse(BaseModel):
    success: bool = Field(description="Успешность выполнения заявки")
    order_id: str = Field(min_length=1, description="Уникальный идентификатор заявки")


class OrderListResponse(BaseModel):
    orders: list[Order] = Field(description="Список ордеров пользователя")
    