from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from src.backend.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    opportunity_type = Column(
        String,
        nullable=False,
    )

    title = Column(
        String,
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    product_id = Column(
        Integer,
        nullable=True,
    )

    related_product_id = Column(
        Integer,
        nullable=True,
    )

    customer_count = Column(
        Integer,
        default=0,
        nullable=False,
    )

    estimated_value = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    confidence = Column(
        String,
        nullable=False,
        default="medium",
    )

    status = Column(
        String,
        nullable=False,
        default="new",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )