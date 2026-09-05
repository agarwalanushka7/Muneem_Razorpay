from sqlalchemy.orm import Session

from src.backend.models.product import Product
from src.backend.models.customer import Customer
from src.backend.models.order import Order


def get_customer_purchase_history(
    db: Session,
    customer_id: int,
):
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if not customer:
        return {
            "success": False,
            "message": "Customer not found",
        }

    orders = (
        db.query(Order)
        .filter(Order.customer_id == customer_id)
        .all()
    )

    purchase_history = []

    for order in orders:
        purchase_history.append(
            {
                "order_id": order.id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "total_amount": order.total_amount,
                "status": order.status,
            }
        )

    return {
        "success": True,
        "customer_id": customer_id,
        "purchase_history": purchase_history,
    }


def find_cross_sell_customers(
    db: Session,
    product_id: int,
    related_product_id: int,
):
    """
    Find customers who purchased the main product
    but have not purchased the related product.
    """

    main_product_customers = (
        db.query(Order.customer_id)
        .filter(
            Order.product_id == product_id
        )
        .distinct()
        .all()
    )

    related_product_customers = (
        db.query(Order.customer_id)
        .filter(
            Order.product_id == related_product_id
        )
        .distinct()
        .all()
    )

    main_customer_ids = {
        customer_id
        for (customer_id,) in main_product_customers
    }

    related_customer_ids = {
        customer_id
        for (customer_id,) in related_product_customers
    }

    opportunity_customer_ids = (
        main_customer_ids - related_customer_ids
    )

    return {
        "success": True,
        "product_id": product_id,
        "related_product_id": related_product_id,
        "customer_ids": list(
            opportunity_customer_ids
        ),
        "customer_count": len(
            opportunity_customer_ids
        ),
    }
def get_product_information(
    db: Session,
    product_id: int,
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        return {
            "success": False,
            "message": "Product not found",
        }

    return {
        "success": True,
        "product": {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "inventory": product.inventory,
            "category": product.category,
        },
    }