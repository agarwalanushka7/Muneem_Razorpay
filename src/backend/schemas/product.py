from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    description: str = ""
    price: float
    inventory: int = 0
    category: str = ""


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    inventory: int
    category: str

    class Config:
        from_attributes = True