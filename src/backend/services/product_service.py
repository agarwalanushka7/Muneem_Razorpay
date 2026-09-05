from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.backend.repositories.product_repository import ProductRepository
from src.backend.schemas.product import ProductCreate


class ProductService:

    def __init__(self):
        self.repository = ProductRepository()

    def get_products(self, db: Session):
        return self.repository.get_all(db)

    def get_product(self, db: Session, product_id: int):
        product = self.repository.get_by_id(db, product_id)

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found",
            )

        return product

    def create_product(self, db: Session, product: ProductCreate):
        return self.repository.create(db, product)

    def update_product(
        self,
        db: Session,
        product_id: int,
        product_data: ProductCreate,
    ):
        product = self.repository.get_by_id(db, product_id)

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found",
            )

        return self.repository.update(
            db,
            product,
            product_data,
        )

    def delete_product(self, db: Session, product_id: int):
        product = self.repository.get_by_id(db, product_id)

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found",
            )

        self.repository.delete(db, product)