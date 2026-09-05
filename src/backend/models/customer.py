from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from src.backend.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=False, index=True)

    phone = Column(String, nullable=True)

    total_orders = Column(Integer, default=0, nullable=False)

    total_spent = Column(Float, default=0.0, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )