from sqlalchemy.orm import Session

from src.backend.models.order import Order


def get_all_orders(db: Session):
    return (
        db.query(Order)
        .order_by(Order.id.desc())
        .all()
    )


def get_order_by_id(
    db: Session,
    order_id: int,
):
    return (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )


def get_orders_by_customer(
    db: Session,
    customer_id: int,
):
    return (
        db.query(Order)
        .filter(Order.customer_id == customer_id)
        .order_by(Order.id.desc())
        .all()
    )


def create_order(
    db: Session,
    customer_id: int,
    product_id: int,
    quantity: int,
    total_amount: float,
):
    order = Order(
        customer_id=customer_id,
        product_id=product_id,
        quantity=quantity,
        total_amount=total_amount,
        status="pending",
        payment_status="pending",
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def update_order_status(
    db: Session,
    order: Order,
    status: str,
):
    order.status = status

    db.commit()
    db.refresh(order)

    return order


def update_payment_status(
    db: Session,
    order: Order,
    payment_status: str,
):
    order.payment_status = payment_status

    db.commit()
    db.refresh(order)

    return order