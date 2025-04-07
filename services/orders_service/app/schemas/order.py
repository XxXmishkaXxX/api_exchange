from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum
from datetime import datetime

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


from pydantic import BaseModel, Field, validator
from typing import Optional
from app.schemas.order import OrderType, Direction


class OrderSchema(BaseModel):
    type: OrderType = Field(description="Тип ордера: 'market' или 'limit'")
    direction: Direction = Field(description="Направление ордера: 'buy' или 'sell'")
    ticker: str = Field(description="Тикер актива для покупки/продажи")
    payment_ticker: Optional[str] = Field("RUB", description="Тикер актива для расчета (по умолчанию 'RUB')")
    qty: int = Field(gt=0, description="Количество должно быть положительным числом")
    price: Optional[float] = Field(None, gt=0, description="Цена для лимитного ордера (должна быть положительной)")

    @validator("price", pre=True, always=True)
    def price_required_for_limit_orders(cls, value, values):
        if values.get("type") == OrderType.LIMIT and value is None:
            raise ValueError("Цена обязательна для лимитных ордеров")
        return value

    @validator("payment_ticker", pre=True, always=True)
    def default_payment_ticker(cls, value):
        return value or "RUB"

    @validator("payment_ticker")
    def tickers_must_be_different(cls, payment_ticker, values):
        ticker = values.get("ticker")
        if ticker and payment_ticker and ticker == payment_ticker:
            raise ValueError("Тикер актива и тикер для расчета не могут совпадать")
        return payment_ticker

    class Config:
        from_attributes = True

    
class OrderCreateResponse(BaseModel):
    success: bool = Field(description="Успешность выполнения заявки")
    order_id: int = Field(description="Уникальный идентификатор заявки")

class OrderCancelResponse(BaseModel):
    success: bool = Field(description="Успешность отмены заявки")

class OrderResponse(BaseModel):
    order_id: int = Field(description="id ордера")
    user_id: int = Field(description="id пользователя")
    status: StatusOrder = Field(description="Статус ордера")
    timestamp: datetime = Field(..., description="Дата и время создания ордера в формате ISO 8601")
    body: OrderSchema

    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    orders: list[OrderResponse] = Field(description="Список ордеров пользователя")
