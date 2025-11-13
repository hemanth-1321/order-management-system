from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime
from enum import Enum

class StatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED" 

class OrderCreate(BaseModel):
    product_name: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)

class OrderRead(BaseModel):
    id: str
    user_id: str
    product_name: str
    amount: float
    status: StatusEnum
    created_at: datetime

    