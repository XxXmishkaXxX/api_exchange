from pydantic import BaseModel, Field
from typing import Annotated
from uuid import UUID

class DepositAssetsSchema(BaseModel):
    user_id: Annotated[UUID, Field(description="id пользователя")]
    ticker: Annotated[str, Field(description="Название тикера")]
    amount: Annotated[int, Field(gt=0, description="Количество должно быть положительным числом")]

class WithdrawAssetsSchema(BaseModel):
    user_id: Annotated[UUID, Field(description="id пользователя")]
    ticker: Annotated[str, Field(description="Название тикера")]
    amount: Annotated[int, Field(gt=0, description="Количество должно быть положительным числом")]
