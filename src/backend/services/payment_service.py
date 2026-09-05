import razorpay

from src.backend.core.config import settings


class PaymentService:
    def __init__(self):
        self.client = razorpay.Client(
            auth=(
                settings.razorpay_key_id,
                settings.razorpay_key_secret,
            )
        )

    def create_payment_order(
        self,
        amount: float,
        receipt: str,
    ):
        amount_in_paise = int(round(amount * 100))

        payment_order = self.client.order.create(
            {
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": receipt,
            }
        )

        return payment_order

    def verify_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ):
        self.client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )

        return True


payment_service = PaymentService()