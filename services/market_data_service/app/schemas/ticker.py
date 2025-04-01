from pydantic import BaseModel, Field

class TickerSchema(BaseModel):
    symbol: str = Field(min_length=3, max_length=5, description="Аббревиатура тикера")
    name: str = Field(min_length=2, max_length=255, description="Название тикера")

    class Config:
        from_attributes = True
