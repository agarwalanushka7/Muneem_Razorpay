import json
from datetime import datetime

from sqlalchemy.orm import Session

from src.backend.models.agent_action import AgentAction
from src.backend.models.payment import Payment
from src.backend.services.razorpay_service import razorpay_service


def sync_payment_statuses(db: Session):
    actions = (
        db.query(AgentAction)
        .filter(
            AgentAction.execution_result.isnot(None)
        )
        .all()
    )

    results = []

    for action in actions:
        try:
            execution_result = action.execution_result

            # execution_result is stored as TEXT in SQLite.
            if isinstance(execution_result, str):
                try:
                    execution_result = json.loads(
                        execution_result
                    )
                except json.JSONDecodeError:
                    results.append({
                        "action_id": action.id,
                        "payment_status": "sync_error",
                        "error": (
                            "Invalid execution_result JSON."
                        ),
                    })
                    continue

            if not isinstance(
                execution_result,
                dict,
            ):
                continue

            razorpay_data = (
                execution_result.get("razorpay")
                or {}
            )

            payment_link_id = (
                execution_result.get(
                    "payment_link_id"
                )
                or razorpay_data.get("id")
            )

            if not payment_link_id:
                continue

            # -------------------------------------------------
            # 1. Get CURRENT payment-link state from Razorpay
            # -------------------------------------------------

            razorpay_payment = (
                razorpay_service.fetch_payment_link(
                    payment_link_id
                )
            )

            if not razorpay_payment.get("success"):
                results.append({
                    "action_id": action.id,
                    "payment_link_id": payment_link_id,
                    "payment_status": "sync_error",
                    "error": razorpay_payment.get(
                        "error",
                        razorpay_payment.get(
                            "message",
                            "Unable to fetch payment status.",
                        ),
                    ),
                })
                continue

            payment_status = str(
                razorpay_payment.get(
                    "payment_status",
                    "pending",
                )
            ).lower()

            # -------------------------------------------------
            # 2. Find the EXISTING Payment database record
            # -------------------------------------------------

            payment_record = (
                db.query(Payment)
                .filter(
                    Payment.payment_link_id
                    == payment_link_id
                )
                .first()
            )

            if payment_record:
                # Keep the original payment amount.
                # Razorpay amount is already returned in INR.
                if razorpay_payment.get("amount") is not None:
                    payment_record.amount = float(
                        razorpay_payment["amount"]
                    )

                payment_record.status = payment_status

                if razorpay_payment.get("currency"):
                    payment_record.currency = (
                        razorpay_payment["currency"]
                    )

                paid_at = razorpay_payment.get("paid_at")
                if paid_at:
                    if paid_at:
                        try:
                            payment_record.paid_at = (
                                datetime.fromisoformat(
                                    str(paid_at)
                                    .replace("Z", "+00:00")
                                ).replace(
                                    tzinfo=None
                                )
                            )
                        except (
                            ValueError,
                            TypeError,
                        ):
                            # Keep the existing timestamp if
                            # Razorpay's timestamp cannot be parsed.
                            pass

                # AgentAction represents MUNEEM execution, while
                # Payment represents the customer payment. Restore
                # any legacy "paid" action state to "executed".
                if payment_status == "paid" and action.status == "paid":
                    action.status = "executed"

                payment_record.updated_at = (
                    datetime.utcnow()
                )

            # -------------------------------------------------
            # 3. Store the latest Razorpay state on AgentAction
            #    as execution metadata.
            #
            #    IMPORTANT:
            #    Do NOT change action.status to "paid".
            #    AgentAction.status describes MUNEEM execution.
            #    Payment.status describes customer payment.
            # -------------------------------------------------

            execution_result["payment_status"] = (
                payment_status
            )

            execution_result["payment"] = {
                "payment_link_id": payment_link_id,
                "status": razorpay_payment.get(
                    "status"
                ),
                "payment_status": payment_status,
                "amount": razorpay_payment.get(
                    "amount"
                ),
                "amount_paid": razorpay_payment.get(
                    "amount_paid"
                ),
                "currency": razorpay_payment.get(
                    "currency",
                    "INR",
                ),
                "reference_id": razorpay_payment.get(
                    "reference_id"
                ),
                "paid_at": razorpay_payment.get(
                    "paid_at"
                ),
            }

            if payment_status == "paid":
                execution_result["paid_at"] = (
                    razorpay_payment.get(
                        "paid_at"
                    )
                )

            # SQLite stores execution_result as TEXT.
            action.execution_result = json.dumps(
                execution_result,
                default=str,
            )

            results.append({
                "action_id": action.id,
                "payment_link_id": payment_link_id,
                "payment_status": payment_status,
                "amount": razorpay_payment.get(
                    "amount"
                ),
                "amount_paid": razorpay_payment.get(
                    "amount_paid"
                ),
            })

        except Exception as exc:
            results.append({
                "action_id": action.id,
                "payment_status": "sync_error",
                "error": str(exc),
            })

    # ---------------------------------------------------------
    # Commit BOTH:
    #   Payment status
    #   AgentAction execution_result
    # ---------------------------------------------------------

    db.commit()

    return results