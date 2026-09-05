from sqlalchemy.orm import Session

from src.backend.models.transaction import Transaction


def get_all_transactions(db: Session):
    return (
        db.query(Transaction)
        .order_by(Transaction.id.desc())
        .all()
    )


def get_transaction_by_id(
    db: Session,
    transaction_id: int,
):
    return (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )


def get_transaction_by_order(
    db: Session,
    order_id: int,
):
    return (
        db.query(Transaction)
        .filter(Transaction.order_id == order_id)
        .first()
    )


def create_transaction(
    db: Session,
    order_id: int,
    amount: float,
    payment_method: str = "razorpay",
):
    transaction = Transaction(
        order_id=order_id,
        amount=amount,
        payment_method=payment_method,
        status="pending",
        payment_id=None,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


def update_transaction_status(
    db: Session,
    transaction: Transaction,
    status: str,
    payment_id: str | None = None,
):
    transaction.status = status

    if payment_id is not None:
        transaction.payment_id = payment_id

    db.commit()
    db.refresh(transaction)

    return transaction