from sqlalchemy.orm import Session

from src.backend.models.product import Product
from src.backend.schemas.product import ProductCreate


class ProductRepository:

    def get_all(self, db: Session):
        return db.query(Product).all()

    def get_by_id(self, db: Session, product_id: int):
        return db.query(Product).filter(Product.id == product_id).first()
    
    def get_by_name(
    self,
    db: Session,
    name: str,
):
     return (
        db.query(Product)
        .filter(Product.name == name)
        .first()
    )
    def create(self, db: Session, product: ProductCreate):
        new_product = Product(
            name=product.name,
            description=product.description,
            price=product.price,
            inventory=product.inventory,
            category=product.category,
        )

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return new_product

    def update(
        self,
        db: Session,
        product: Product,
        product_data: ProductCreate,
    ):
        product.name = product_data.name
        product.description = product_data.description
        product.price = product_data.price
        product.inventory = product_data.inventory
        product.category = product_data.category

        db.commit()
        db.refresh(product)

        return product

    def delete(self, db: Session, product: Product):
        db.delete(product)
        db.commit()