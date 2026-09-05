from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.backend.database import get_db

from src.backend.models.customer import Customer
from src.backend.models.product import Product

from src.backend.schemas.order import (
    OrderCreate,
    OrderResponse,
)

from src.backend.repositories.order_repository import (
    get_all_orders,
    get_order_by_id,
    get_orders_by_customer,
    create_order,
)


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.get(
    "/",
    response_model=list[OrderResponse],
)
def read_orders(
    db: Session = Depends(get_db),
):
    return get_all_orders(db)


@router.get(
    "/customer/{customer_id}",
    response_model=list[OrderResponse],
)
def read_customer_orders(
    customer_id: int,
    db: Session = Depends(get_db),
):
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return get_orders_by_customer(
        db,
        customer_id,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def read_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = get_order_by_id(
        db,
        order_id,
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return order


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
):
    # Validate quantity
    if order_data.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than 0",
        )

    # Find customer
    customer = (
        db.query(Customer)
        .filter(Customer.id == order_data.customer_id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # Find product
    product = (
        db.query(Product)
        .filter(Product.id == order_data.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Check inventory
    if product.inventory < order_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient inventory",
        )

    # Calculate total on backend
    total_amount = (
        product.price * order_data.quantity
    )

    # Reduce inventory
    product.inventory -= order_data.quantity

    # Create order
    order = create_order(
        db=db,
        customer_id=order_data.customer_id,
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        total_amount=total_amount,
    )

    return order