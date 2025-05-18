from typing import Annotated
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: Annotated[str, Field(min_length=1)]
