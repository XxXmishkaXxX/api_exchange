from pydantic import BaseModel, Field

class AssetSchema(BaseModel):
    ticker: str = Field(min_length=3, max_length=5, description="Тикер актива")
    name: str = Field(min_length=2, max_length=255, description="Название актива")

    class Config:
        from_attributes = True
