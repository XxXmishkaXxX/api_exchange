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

class StatusOrder(str, Enum):
    NEW = "new"  # Новый ордер
    FILLED = "filled"  # Выполнен
    PENDING = "pending"  # Ожидает выполнения
    REJECTED = "rejected"  # Отклонен


class TickerSchema(BaseModel):
    id: int = Field(description="ID тикера")
    symbol: str = Field(min_length=3, max_length=5, description="Аббревиатура тикера")
    name: str = Field(min_length=2, max_length=255, description="Название тикера")

    class Config:
        from_attributes = True

class OrderSchema(BaseModel):
    type: OrderType = Field(description="Тип ордера: 'market' или 'limit'")
    direction: Direction = Field(description="Направление ордера: 'buy' или 'sell'")
    status: StatusOrder = Field(description="Статус ордера")
    ticker_id: int = Field(None, description="id тикера")
    qty: int = Field(gt=0, description="Количество должно быть положительным числом")
    price: Optional[float] = Field(None, gt=0, description="Цена для лимитного ордера (должна быть положительной)")

    @validator("price", pre=True, always=True)
    def price_required_for_limit_orders(cls, value, values):
        if values.get("type") == OrderType.LIMIT and value is None:
            raise ValueError("Цена обязательна для лимитных ордеров")
        return value
    
    class Config:
        from_attributes = True
    
class OrderCreateResponse(BaseModel):
    success: bool = Field(description="Успешность выполнения заявки")
    order_id: int = Field(description="Уникальный идентификатор заявки")

class OrderCancelResponse(BaseModel):
    success: bool = Field(description="Успешность отмены заявки")

class OrderResponse(BaseModel):
    order: OrderSchema = Field(description="Отдельный ордер пользователя")

class OrderListResponse(BaseModel):
    orders: list[OrderSchema] = Field(description="Список ордеров пользователя")
