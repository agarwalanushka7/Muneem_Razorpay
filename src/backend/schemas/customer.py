from datetime import datetime

from pydantic import BaseModel


class CustomerCreate(BaseModel):
    name: str
    email: str
    phone: str = ""


class CustomerResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    total_orders: int
    total_spent: float
    created_at: datetime

    class Config:
        from_attributes = True