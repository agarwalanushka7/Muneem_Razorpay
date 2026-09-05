from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer

from src.backend.database import Base


class AIPolicy(Base):
    __tablename__ = "ai_policies"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    max_auto_action_amount = Column(
        Float,
        nullable=False,
        default=1000.0,
    )

    max_discount_amount = Column(
        Float,
        nullable=False,
        default=500.0,
    )

    max_discount_percentage = Column(
        Float,
        nullable=False,
        default=10.0,
    )

    auto_actions_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    require_approval_above_limit = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )