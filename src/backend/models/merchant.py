from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from src.backend.database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    business_name = Column(
        String,
        nullable=False,
    )

    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    password = Column(
        String,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )