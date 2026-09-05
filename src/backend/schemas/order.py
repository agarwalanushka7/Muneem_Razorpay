from datetime import datetime

from pydantic import BaseModel


class OrderCreate(BaseModel):
    customer_id: int
    product_id: int
    quantity: int


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    product_id: int
    quantity: int
    total_amount: float
    status: str
    payment_status: str
    created_at: datetime

    class Config:
        from_attributes = True