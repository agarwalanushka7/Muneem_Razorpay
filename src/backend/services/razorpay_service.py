import time

import razorpay

from src.backend.core.config import settings


class RazorpayService:

    def __init__(self):
        if not settings.razorpay_key_id:
            raise ValueError(
                "RAZORPAY_KEY_ID is not configured."
            )

        if not settings.razorpay_key_secret:
            raise ValueError(
                "RAZORPAY_KEY_SECRET is not configured."
            )

        self.client = razorpay.Client(
            auth=(
                settings.razorpay_key_id,
                settings.razorpay_key_secret,
            )
        )

    def create_payment_link(
        self,
        amount: float,
        reference_id: str,
        description: str,
    ):
        # -----------------------------------------------------
        # VALIDATE AMOUNT
        # -----------------------------------------------------

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return {
                "success": False,
                "provider": "razorpay",
                "message": "Invalid payment amount.",
            }

        if amount <= 0:
            return {
                "success": False,
                "provider": "razorpay",
                "message": (
                    "Payment amount must be greater than zero."
                ),
            }

        amount_in_paise = int(round(amount * 100))

        if amount_in_paise < 100:
            return {
                "success": False,
                "provider": "razorpay",
                "message": (
                    "Razorpay payment links require a minimum "
                    "amount of 100 paise for INR."
                ),
            }

        # -----------------------------------------------------
        # UNIQUE REFERENCE ID
        #
        # Razorpay requires reference_id to be unique.
        # This also makes retries safe after a previous failed
        # or interrupted request.
        # -----------------------------------------------------

        base_reference = str(
            reference_id or "muneem_payment"
        ).strip()

        # Keep the reference within Razorpay's 40-character
        # limit while guaranteeing uniqueness.
        unique_reference_id = (
            f"{base_reference[:22]}_{int(time.time() * 1000)}"
        )

        # -----------------------------------------------------
        # PAYMENT LINK REQUEST
        # -----------------------------------------------------

        payload = {
            "amount": amount_in_paise,
            "currency": "INR",
            "accept_partial": False,
            "description": str(description or "MUNEEM payment")[:2048],
            "reference_id": unique_reference_id,
            "reminder_enable": True,
        }

        # -----------------------------------------------------
        # CREATE PAYMENT LINK
        # -----------------------------------------------------

        try:
            payment_link = self.client.payment_link.create(
                payload
            )

        except Exception as exc:
            # Never hide the Razorpay error. The previous
            # implementation returned only a generic message,
            # which made the real configuration/API problem
            # impossible to diagnose.
            error_text = str(exc).strip()

            return {
                "success": False,
                "provider": "razorpay",
                "stage": "payment_link_creation",
                "message": (
                    "Unable to create Razorpay payment link."
                ),
                "error": error_text or repr(exc),
                "reference_id": unique_reference_id,
                "amount": amount,
                "currency": "INR",
            }

        # -----------------------------------------------------
        # VALIDATE RAZORPAY RESPONSE
        # -----------------------------------------------------

        payment_link_id = payment_link.get("id")
        short_url = payment_link.get("short_url")

        if not payment_link_id or not short_url:
            return {
                "success": False,
                "provider": "razorpay",
                "stage": "payment_link_response",
                "message": (
                    "Razorpay created an incomplete payment-link "
                    "response."
                ),
                "response": payment_link,
                "reference_id": unique_reference_id,
            }

        # -----------------------------------------------------
        # SUCCESS
        # -----------------------------------------------------

        return {
            "success": True,
            "provider": "razorpay",
            "type": "payment_link",
            "id": payment_link_id,
            "short_url": short_url,
            "status": payment_link.get("status"),
            "amount": amount,
            "amount_in_paise": amount_in_paise,
            "currency": payment_link.get("currency", "INR"),
            "reference_id": unique_reference_id,
        }


    def fetch_payment_link(
        self,
        payment_link_id: str,
    ):
        """
        Fetch the current Razorpay Payment Link state.

        amount_paid is used to determine whether the customer
        actually completed payment.
        """
        payment_link_id = str(
            payment_link_id or ""
        ).strip()

        if not payment_link_id:
            return {
                "success": False,
                "provider": "razorpay",
                "message": "Payment link ID is missing.",
            }

        try:
            result = self.client.payment_link.fetch(
                payment_link_id
            )

            amount = float(
                result.get("amount", 0) or 0
            ) / 100.0

            amount_paid = float(
                result.get("amount_paid", 0) or 0
            ) / 100.0

            raw_status = str(
                result.get("status", "")
            ).lower().strip()

            if amount > 0 and amount_paid >= amount:
                payment_status = "paid"
            elif raw_status in {
                "cancelled",
                "canceled",
                "expired",
            }:
                payment_status = raw_status
            elif raw_status == "partially_paid":
                payment_status = "partially_paid"
            else:
                payment_status = "pending"

            return {
                "success": True,
                "provider": "razorpay",
                "payment_link_id": payment_link_id,
                "payment_status": payment_status,
                "status": raw_status,
                "amount": amount,
                "amount_paid": amount_paid,
                "currency": result.get("currency", "INR"),
                "reference_id": result.get("reference_id"),
                "created_at": result.get("created_at"),
                "paid_at": result.get("paid_at")
                    or result.get("updated_at"),
                "raw": result,
            }

        except Exception as exc:
            return {
                "success": False,
                "provider": "razorpay",
                "message": "Unable to fetch Razorpay payment-link status.",
                "error": str(exc).strip() or repr(exc),
                "payment_link_id": payment_link_id,
            }


razorpay_service = RazorpayService()
