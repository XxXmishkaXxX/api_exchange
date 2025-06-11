from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated

class AssetSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: Annotated[str, Field(min_length=3, max_length=10, pattern="^[A-Z]{2,10}$",description="Тикер актива")]
    name: Annotated[str, Field(min_length=2, max_length=255, description="Название актива")]
