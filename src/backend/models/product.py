from sqlalchemy import Column, Float, Integer, String, Text
from src.backend.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    price = Column(Float, nullable=False)
    inventory = Column(Integer, default=0)
    category = Column(String(100), default="")