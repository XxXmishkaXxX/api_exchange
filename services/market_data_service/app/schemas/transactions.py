from pydantic import BaseModel, Field
from typing import List, Optional, Annotated
from datetime import datetime


class Transaction(BaseModel):
    ticker: str
    price: int
    amount: int
    timestamp: datetime
