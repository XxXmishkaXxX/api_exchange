from pydantic import BaseModel, Field
from typing import Annotated
from datetime import datetime

class Transaction(BaseModel):
    ticker: Annotated[str, Field(description="Тикер актива")]
    price: Annotated[int, Field(gt=0, description="Цена сделки (должна быть положительной)")]
    amount: Annotated[int, Field(gt=0, description="Количество в сделке (должно быть положительным)")]
    timestamp: Annotated[datetime, Field(description="Время сделки в формате ISO 8601")]
