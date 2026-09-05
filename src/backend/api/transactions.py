from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.backend.database import get_db

from src.backend.models.order import Order

from src.backend.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
)

from src.backend.repositories.transaction_repository import (
    get_all_transactions,
    get_transaction_by_id,
    get_transaction_by_order,
    create_transaction,
)


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)


@router.get(
    "/",
    response_model=list[TransactionResponse],
)
def read_transactions(
    db: Session = Depends(get_db),
):
    return get_all_transactions(db)


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def read_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    transaction = get_transaction_by_id(
        db,
        transaction_id,
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return transaction


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
):
    # Find the order
    order = (
        db.query(Order)
        .filter(Order.id == transaction_data.order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Prevent duplicate transactions
    existing_transaction = get_transaction_by_order(
        db,
        transaction_data.order_id,
    )

    if existing_transaction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction already exists for this order",
        )

    # Only valid payment methods
    allowed_methods = ["razorpay"]

    if transaction_data.payment_method not in allowed_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported payment method",
        )

    # Create transaction using the order amount
    transaction = create_transaction(
        db=db,
        order_id=order.id,
        amount=order.total_amount,
        payment_method=transaction_data.payment_method,
    )

    return transaction