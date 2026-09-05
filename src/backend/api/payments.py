from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.backend.database import get_db

from src.backend.repositories.order_repository import (
    get_order_by_id,
)

from src.backend.repositories.payment_repository import (
    create_payment,
    get_all_payments,
    get_payment_by_id,
    get_payment_by_action_id,
    update_payment_status,
)

from src.backend.services.payment_service import (
    payment_service,
)


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


# =========================================================
# REQUEST SCHEMA
# =========================================================

class PaymentVerification(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    transaction_id: int


# =========================================================
# GET ALL PAYMENTS
# =========================================================

@router.get("/")
def get_payments(
    db: Session = Depends(get_db),
):
    payments = get_all_payments(db)

    return [
        {
            "id": payment.id,
            "agent_action_id": payment.agent_action_id,
            "provider": payment.provider,
            "provider_payment_id": payment.provider_payment_id,
            "provider_order_id": payment.provider_order_id,
            "payment_link_id": payment.payment_link_id,
            "payment_url": payment.payment_url,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "paid_at": payment.paid_at,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
        }
        for payment in payments
    ]


# =========================================================
# CREATE RAZORPAY ORDER
# =========================================================

@router.post("/create/{order_id}")
def create_order_payment(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = get_order_by_id(
        db,
        order_id,
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    amount = float(order.total_amount)

    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Order amount must be greater than zero",
        )

    try:
        razorpay_order = (
            payment_service.create_payment_order(
                amount=amount,
                receipt=f"order_{order.id}",
            )
        )

        payment = create_payment(
            db=db,
            agent_action_id=None,
            provider="razorpay",
            payment_link_id=None,
            payment_url=None,
            provider_order_id=razorpay_order["id"],
            provider_payment_id=None,
            amount=amount,
            currency="INR",
            status="created",
        )

        return {
            "success": True,
            "order_id": order.id,
            "transaction_id": payment.id,
            "razorpay_order_id": razorpay_order["id"],
            "amount": razorpay_order["amount"],
            "currency": razorpay_order["currency"],
            "key_id": payment_service.client.auth[0],
        }

    except Exception as error:
        print(
            "Razorpay order creation error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to create Razorpay order",
        )


# =========================================================
# VERIFY PAYMENT
# =========================================================

@router.post("/verify")
def verify_payment(
    request: PaymentVerification,
    db: Session = Depends(get_db),
):
    payment = get_payment_by_id(
        db,
        request.transaction_id,
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment transaction not found",
        )

    try:
        payment_service.verify_payment(
            razorpay_order_id=request.razorpay_order_id,
            razorpay_payment_id=request.razorpay_payment_id,
            razorpay_signature=request.razorpay_signature,
        )

        update_payment_status(
            db=db,
            payment=payment,
            status="paid",
            provider_payment_id=request.razorpay_payment_id,
            provider_order_id=request.razorpay_order_id,
            paid_at=datetime.utcnow(),
        )

        return {
            "success": True,
            "payment_id": payment.id,
            "status": "paid",
            "message": "Payment verified successfully",
        }

    except Exception as error:
        print(
            "Razorpay payment verification error:",
            error,
        )

        update_payment_status(
            db=db,
            payment=payment,
            status="failed",
        )

        raise HTTPException(
            status_code=400,
            detail="Payment verification failed",
        )


# =========================================================
# GET PAYMENT BY ID
# =========================================================

@router.get("/{payment_id}")
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
):
    payment = get_payment_by_id(
        db,
        payment_id,
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return {
        "id": payment.id,
        "agent_action_id": payment.agent_action_id,
        "provider": payment.provider,
        "provider_payment_id": payment.provider_payment_id,
        "provider_order_id": payment.provider_order_id,
        "payment_link_id": payment.payment_link_id,
        "payment_url": payment.payment_url,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "paid_at": payment.paid_at,
        "created_at": payment.created_at,
        "updated_at": payment.updated_at,
    }


# =========================================================
# GET PAYMENT FOR AGENT ACTION
# =========================================================

@router.get("/action/{action_id}")
def get_payment_for_action(
    action_id: int,
    db: Session = Depends(get_db),
):
    payment = get_payment_by_action_id(
        db,
        action_id,
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found for this action",
        )

    return {
        "id": payment.id,
        "agent_action_id": payment.agent_action_id,
        "provider": payment.provider,
        "provider_payment_id": payment.provider_payment_id,
        "provider_order_id": payment.provider_order_id,
        "payment_link_id": payment.payment_link_id,
        "payment_url": payment.payment_url,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "paid_at": payment.paid_at,
        "created_at": payment.created_at,
        "updated_at": payment.updated_at,
    }