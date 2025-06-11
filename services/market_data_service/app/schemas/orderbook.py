from pydantic import BaseModel, Field
from typing import List, Optional, Annotated

class Order(BaseModel):
    price: Annotated[int, Field(description="Цена заявки")]
    qty: Annotated[int, Field(description="Количество в заявке")]

class OrderBookErrorResponse(BaseModel):
    detail: Annotated[str, Field(description="Описание ошибки")]

class OrderBookResponse(BaseModel):
    bid_levels: Annotated[List[Order], Field(description="Список заявок на покупку")]
    ask_levels: Annotated[List[Order], Field(description="Список заявок на продажу")]

class OrderBookRequest(BaseModel):
    ticker: Annotated[str, Field(description="Базовый тикер, например BTC")]
    pair: Annotated[Optional[str], Field(default=None, description="Пара к тикеру, например USDT. По умолчанию RUB")]
    limit: Annotated[
        Optional[int],
        Field(default=None, ge=1, le=1000, description="Максимальное количество заявок с каждой стороны")
    ]

    @property
    def ticker_pair(self) -> str:
        return f"{self.ticker}/{self.pair or 'RUB'}"
