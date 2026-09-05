import json

from sqlalchemy.orm import Session

from src.backend.models.customer import Customer
from src.backend.models.product import Product
from src.backend.models.order import Order

from src.backend.repositories.agent_action_repository import (
    update_agent_action_status,
)

from src.backend.repositories.payment_repository import (
    create_payment,
)

from src.backend.services.razorpay_service import (
    razorpay_service,
)

from src.backend.services.email_service import (
    email_service,
)


class ActionExecutor:

    def execute(
        self,
        db: Session,
        action,
    ):

        # =====================================================
        # VALIDATE ACTION
        # =====================================================

        if action is None:
            return {
                "success": False,
                "message": "Agent action not found.",
            }

        if action.status == "rejected":
            return {
                "success": False,
                "message": "Rejected actions cannot be executed.",
            }

        if action.status == "pending_approval":
            return {
                "success": False,
                "message": (
                    "Merchant approval is required "
                    "before execution."
                ),
            }

        if action.status in {"executed", "paid"}:
            return {
                "success": True,
                "already_executed": True,
                "action_id": action.id,
                "status": action.status,
                "message": "This action has already been executed.",
            }

        # =====================================================
        # NO ACTION
        # =====================================================

        if action.action_type == "no_action":

            execution_result = {
                "success": True,
                "type": "no_action",
                "message": "No action was required.",
            }

            update_agent_action_status(
                db=db,
                action=action,
                status="executed",
                execution_result=json.dumps(
                    execution_result,
                    default=str,
                ),
            )

            db.commit()

            return execution_result

        # =====================================================
        # APPROVAL CHECK
        # =====================================================

        if (
            action.approval_required
            and action.status != "approved"
        ):
            return {
                "success": False,
                "message": (
                    "This action requires merchant approval."
                ),
            }

        # =====================================================
        # LOAD CUSTOMER
        # =====================================================

        customer = None

        if getattr(action, "customer_id", None):
            customer = (
                db.query(Customer)
                .filter(Customer.id == action.customer_id)
                .first()
            )

        # =====================================================
        # LOAD PRODUCT
        # =====================================================

        product = None

        if getattr(action, "product_id", None):
            product = (
                db.query(Product)
                .filter(Product.id == action.product_id)
                .first()
            )

        # =====================================================
        # VALIDATE CUSTOMER
        # =====================================================

        if not customer:
            return {
                "success": False,
                "message": "Customer could not be found.",
            }

        if not customer.email:
            return {
                "success": False,
                "message": "Customer does not have an email address.",
            }

        # =====================================================
        # VALIDATE PRODUCT
        # =====================================================

        if not product:
            return {
                "success": False,
                "message": "Product could not be found.",
            }

        # =====================================================
        # PURCHASE HISTORY
        # =====================================================

        purchase_history = []

        orders = (
            db.query(Order)
            .filter(Order.customer_id == customer.id)
            .order_by(Order.created_at.desc())
            .all()
        )

        for order in orders:

            purchased_product = None

            if getattr(order, "product_id", None):
                purchased_product = (
                    db.query(Product)
                    .filter(Product.id == order.product_id)
                    .first()
                )

            if not purchased_product:
                continue

            purchase_history.append(
                {
                    "order_id": order.id,
                    "product_id": purchased_product.id,
                    "product_name": purchased_product.name,
                    "quantity": getattr(order, "quantity", 1) or 1,
                    "amount": float(
                        getattr(order, "total_amount", 0) or 0
                    ),
                    # IMPORTANT: datetime is converted to a JSON-safe string.
                    "created_at": (
                        order.created_at.isoformat()
                        if order.created_at
                        else None
                    ),
                }
            )

        # =====================================================
        # FINAL AMOUNT
        # =====================================================

        final_amount = (
            action.final_amount
            if action.final_amount is not None
            else action.action_amount
        )

        try:
            final_amount = float(final_amount or 0)

        except (ValueError, TypeError):
            return {
                "success": False,
                "message": "Invalid payment amount.",
            }

        if final_amount <= 0:
            return {
                "success": False,
                "message": "Payment amount must be greater than zero.",
            }

        # =====================================================
        # OFFER VALUES
        # =====================================================

        original_amount = float(
            getattr(action, "original_amount", 0) or 0
        )

        discount_percentage = float(
            getattr(action, "discount_percentage", 0) or 0
        )

        discount_amount = float(
            getattr(action, "discount_amount", 0) or 0
        )

        # =====================================================
        # DESCRIPTION
        # =====================================================

        description = (
            f"MUNEEM personalized offer - {product.name}"
        )

        # =====================================================
        # RAZORPAY
        # =====================================================

        reference_id = f"muneem_action_{action.id}"

        try:
            razorpay_result = (
                razorpay_service.create_payment_link(
                    amount=final_amount,
                    reference_id=reference_id,
                    description=description,
                )
            )

        except Exception as exc:
            razorpay_result = {
                "success": False,
                "message": "Razorpay payment link creation failed.",
                "error": str(exc),
            }

        if not razorpay_result.get("success", False):

            execution_result = {
                "success": False,
                "stage": "razorpay",
                "status": "failed",
                "message": razorpay_result.get(
                    "message",
                    "Unable to create Razorpay payment link.",
                ),
                "error": razorpay_result.get("error"),
            }

            update_agent_action_status(
                db=db,
                action=action,
                status="failed",
                execution_result=json.dumps(
                    execution_result,
                    default=str,
                ),
            )

            db.commit()

            return execution_result

        payment_url = razorpay_result.get("short_url")

        if not payment_url:

            execution_result = {
                "success": False,
                "stage": "razorpay",
                "status": "failed",
                "message": "Razorpay returned no payment URL.",
            }

            update_agent_action_status(
                db=db,
                action=action,
                status="failed",
                execution_result=json.dumps(
                    execution_result,
                    default=str,
                ),
            )

            db.commit()

            return execution_result

        # =====================================================
        # SAVE PAYMENT
        # =====================================================

        try:

            payment = create_payment(
                db=db,
                agent_action_id=action.id,
                provider="razorpay",
                payment_link_id=razorpay_result.get("id"),
                payment_url=payment_url,
                provider_order_id=None,
                provider_payment_id=None,
                amount=final_amount,
                currency="INR",
                status="created",
            )

            db.flush()

        except Exception as exc:

            db.rollback()

            return {
                "success": False,
                "stage": "payment_record",
                "status": "failed",
                "message": "Payment record could not be saved.",
                "error": str(exc),
                "payment_link": payment_url,
            }

        # =====================================================
        # SEND EMAIL
        # =====================================================

        try:

            email_result = (
                email_service.send_offer_email(
                    to_email=customer.email,
                    customer_name=customer.name,
                    product_name=product.name,
                    original_amount=original_amount,
                    discount_percentage=discount_percentage,
                    discount_amount=discount_amount,
                    final_amount=final_amount,
                    payment_link=payment_url,
                    purchase_history=purchase_history,
                )
            )

        except Exception as exc:

            email_result = {
                "success": False,
                "sent": False,
                "message": "Email sending failed.",
                "error": str(exc),
            }

        # =====================================================
        # EMAIL FAILED
        # =====================================================

        if not email_result.get("success", False):

            execution_result = {
                "success": False,
                "stage": "email",
                "status": "approved_email_failed",

                "payment_id": payment.id,
                "payment_link": payment_url,
                "razorpay": razorpay_result,

                "customer": {
                    "id": customer.id,
                    "name": customer.name,
                    "email": customer.email,
                },

                "product": {
                    "id": product.id,
                    "name": product.name,
                },

                "offer": {
                    "original_amount": original_amount,
                    "discount_percentage": discount_percentage,
                    "discount_amount": discount_amount,
                    "final_amount": final_amount,
                },

                "email": email_result,
                "purchase_history": purchase_history,
            }

            update_agent_action_status(
                db=db,
                action=action,
                status="approved",
                execution_result=json.dumps(
                    execution_result,
                    default=str,
                ),
            )

            db.commit()

            return {
                "success": False,
                "action_id": action.id,
                "status": "approved_email_failed",
                "payment_id": payment.id,
                "payment_link": payment_url,
                "razorpay": razorpay_result,
                "email": email_result,
                "offer": execution_result["offer"],
                "message": (
                    "Payment link created, "
                    "but the customer email could not be sent."
                ),
            }

        # =====================================================
        # SUCCESS
        # =====================================================

        execution_result = {
            "success": True,
            "status": "executed",

            "payment_id": payment.id,
            "payment_link": payment_url,
            "razorpay": razorpay_result,

            "customer": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
            },

            "product": {
                "id": product.id,
                "name": product.name,
            },

            "offer": {
                "original_amount": original_amount,
                "discount_percentage": discount_percentage,
                "discount_amount": discount_amount,
                "final_amount": final_amount,
            },

            "email": email_result,
            "customer_message": action.customer_message,
            "purchase_history": purchase_history,
        }

        update_agent_action_status(
            db=db,
            action=action,
            status="executed",
            execution_result=json.dumps(
                execution_result,
                default=str,
            ),
        )

        db.commit()

        return {
            "success": True,
            "action_id": action.id,
            "status": "executed",
            "payment_id": payment.id,
            "payment_link": payment_url,
            "razorpay": razorpay_result,
            "email": email_result,
            "offer": execution_result["offer"],
            "purchase_history": purchase_history,
            "message": (
                "Personalized offer approved, "
                "Razorpay payment link created, "
                "and email sent successfully."
            ),
        }


action_executor = ActionExecutor()
