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


class Order(Base):
    __tablename__ = "orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )

    quantity = Column(
        Integer,
        nullable=False,
        default=1,
    )

    total_amount = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    status = Column(
        String,
        nullable=False,
        default="pending",
    )

    payment_status = Column(
        String,
        nullable=False,
        default="pending",
    )

    # Sales channel / platform
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