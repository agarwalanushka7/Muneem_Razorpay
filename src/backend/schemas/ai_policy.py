from datetime import datetime

from pydantic import BaseModel, Field


class AIPolicyUpdate(BaseModel):
    max_auto_action_amount: float = Field(
        default=1000.0,
        ge=0,
    )

    max_discount_amount: float = Field(
        default=500.0,
        ge=0,
    )

    max_discount_percentage: float = Field(
        default=10.0,
        ge=0,
        le=100,
    )

    auto_actions_enabled: bool = False

    require_approval_above_limit: bool = True


class AIPolicyResponse(BaseModel):
    id: int
    max_auto_action_amount: float
    max_discount_amount: float
    max_discount_percentage: float
    auto_actions_enabled: bool
    require_approval_above_limit: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True