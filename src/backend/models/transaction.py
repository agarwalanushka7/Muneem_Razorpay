from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from src.backend.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
    )

    amount = Column(
        Float,
        nullable=False,
    )

    payment_method = Column(
        String,
        nullable=False,
        default="razorpay",
    )

    status = Column(
        String,
        nullable=False,
        default="pending",
    )

    payment_id = Column(
        String,
        nullable=True,
    )

    # Payment source / platform
    platform = Column(
        String,
        nullable=False,
        default="direct",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )