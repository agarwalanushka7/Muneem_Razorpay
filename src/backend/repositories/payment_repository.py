from datetime import datetime

from sqlalchemy.orm import Session

from src.backend.models.payment import Payment


def create_payment(
    db: Session,
    agent_action_id: int | None,
    provider: str,
    payment_link_id: str | None,
    payment_url: str | None,
    provider_order_id: str | None,
    provider_payment_id: str | None,
    amount: float,
    currency: str = "INR",
    status: str = "created",
):
    payment = Payment(
        agent_action_id=agent_action_id,
        provider=provider,
        payment_link_id=payment_link_id,
        payment_url=payment_url,
        provider_order_id=provider_order_id,
        provider_payment_id=provider_payment_id,
        amount=amount,
        currency=currency,
        status=status,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


def get_payment_by_id(
    db: Session,
    payment_id: int,
):
    return (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .first()
    )


def get_payment_by_action_id(
    db: Session,
    agent_action_id: int,
):
    return (
        db.query(Payment)
        .filter(
            Payment.agent_action_id == agent_action_id
        )
        .first()
    )


def get_payment_by_link_id(
    db: Session,
    payment_link_id: str,
):
    return (
        db.query(Payment)
        .filter(
            Payment.payment_link_id == payment_link_id
        )
        .first()
    )


def get_payment_by_provider_payment_id(
    db: Session,
    provider_payment_id: str,
):
    return (
        db.query(Payment)
        .filter(
            Payment.provider_payment_id
            == provider_payment_id
        )
        .first()
    )


def update_payment_status(
    db: Session,
    payment: Payment,
    status: str,
    provider_payment_id: str | None = None,
    provider_order_id: str | None = None,
    paid_at: datetime | None = None,
):
    payment.status = status

    if provider_payment_id is not None:
        payment.provider_payment_id = (
            provider_payment_id
        )

    if provider_order_id is not None:
        payment.provider_order_id = (
            provider_order_id
        )

    if paid_at is not None:
        payment.paid_at = paid_at

    db.commit()
    db.refresh(payment)

    return payment


def get_all_payments(db: Session):
    return (
        db.query(Payment)
        .order_by(Payment.id.desc())
        .all()
    )