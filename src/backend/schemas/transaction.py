from datetime import datetime

from pydantic import BaseModel


class TransactionCreate(BaseModel):
    order_id: int
    payment_method: str = "razorpay"


class TransactionResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    payment_method: str
    status: str
    payment_id: str | None
    created_at: datetime

    class Config:
        from_attributes = True