from pydantic import BaseModel, Field, validator
from typing import Optional


class DepositAssetsSchema(BaseModel):
    user_id: int = Field(description="id пользователя")
    ticker: str = Field(description="Название тикера")
    amount: int = Field(gt=0, )

class WithdrawAssetsSchema(BaseModel):
    user_id: int = Field(description="id пользователя")
    ticker: str = Field(description="Название тикера")
    amount: int = Field(gt=0, )

