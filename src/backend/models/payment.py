from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from src.backend.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    agent_action_id = Column(
        Integer,
        ForeignKey("agent_actions.id"),
        nullable=True,
    )

    provider = Column(
        String,
        nullable=False,
        default="razorpay",
    )

    provider_payment_id = Column(
        String,
        nullable=True,
        index=True,
    )

    provider_order_id = Column(
        String,
        nullable=True,
        index=True,
    )

    payment_link_id = Column(
        String,
        nullable=True,
        index=True,
    )

    payment_url = Column(
        String,
        nullable=True,
    )

    amount = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    currency = Column(
        String,
        nullable=False,
        default="INR",
    )

    status = Column(
        String,
        nullable=False,
        default="created",
    )

    paid_at = Column(
        DateTime,
        nullable=True,
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