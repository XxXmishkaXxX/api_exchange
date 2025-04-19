from pydantic import BaseModel, Field
from typing import List, Optional, Annotated


class Order(BaseModel):
    price: int
    amount: int

class OrderBookErrorResponse(BaseModel):
    detail: str

class OrderBookResponse(BaseModel):
    bids: List[Order]
    asks: List[Order]


class OrderBookRequest(BaseModel):
    ticker: Annotated[str, Field(description="Базовый тикер, например BTC")]
    pair: Annotated[Optional[str], Field(description="Пара к тикеру, например USDT. По умолчанию RUB")] = None
    limit: Annotated[
        Optional[int],
        Field(ge=1, le=1000, description="Максимальное количество заявок с каждой стороны")
    ] = None

    @property
    def ticker_pair(self) -> str:
        return f"{self.ticker}/{self.pair or 'RUB'}"