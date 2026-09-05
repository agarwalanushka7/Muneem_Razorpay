from sqlalchemy.orm import Session

from src.backend.models.customer import Customer
from src.backend.models.product import Product


class PersonalizedOfferService:

    def build_offer(
        self,
        db: Session,
        customer_id: int,
        product_id: int,
        discount_percentage: float = 0.0,
        reason: str = "",
    ):
        # =====================================================
        # 1. GET CUSTOMER
        # =====================================================

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == customer_id
            )
            .first()
        )

        if not customer:
            return {
                "success": False,
                "message": "Customer not found.",
            }

        # =====================================================
        # 2. GET PRODUCT
        # =====================================================

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id
            )
            .first()
        )

        if not product:
            return {
                "success": False,
                "message": "Product not found.",
            }

        # =====================================================
        # 3. CHECK INVENTORY
        # =====================================================

        if product.inventory <= 0:
            return {
                "success": False,
                "message": (
                    f"{product.name} is currently "
                    "out of stock."
                ),
            }

        # =====================================================
        # 4. CALCULATE PRICE
        # =====================================================

        original_amount = round(
            float(product.price),
            2,
        )

        try:
            discount_percentage = float(
                discount_percentage or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            discount_percentage = 0.0

        # Keep discount within a safe range.
        discount_percentage = max(
            0.0,
            min(
                discount_percentage,
                100.0,
            ),
        )

        discount_amount = round(
            original_amount
            * discount_percentage
            / 100,
            2,
        )

        final_amount = round(
            original_amount
            - discount_amount,
            2,
        )

        # =====================================================
        # 5. BUILD CUSTOMER MESSAGE
        # =====================================================

        if discount_percentage > 0:

            message = (
                f"Hi {customer.name} 👋\n\n"
                f"Based on your recent purchase, "
                f"we thought you might like our "
                f"{product.name}.\n\n"
                f"We've unlocked a "
                f"{discount_percentage:g}% "
                f"personalized offer for you.\n\n"
                f"Your price: "
                f"₹{final_amount:,.0f}\n\n"
            )

        else:

            message = (
                f"Hi {customer.name} 👋\n\n"
                f"Based on your recent purchase, "
                f"we thought you might like our "
                f"{product.name}.\n\n"
                f"Your price: "
                f"₹{final_amount:,.0f}\n\n"
            )

        # Add the reason from MUNEEM's analysis.
        if reason:
            message += f"{reason}\n\n"

        message += (
            "Complete your purchase using "
            "the secure payment link below."
        )

        # =====================================================
        # 6. RETURN COMPLETE OFFER
        # =====================================================

        return {
            "success": True,

            "customer": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
            },

            "product": {
                "id": product.id,
                "name": product.name,
                "price": original_amount,
                "inventory": product.inventory,
            },

            "original_amount": original_amount,

            "discount_percentage": (
                discount_percentage
            ),

            "discount_amount": (
                discount_amount
            ),

            "final_amount": final_amount,

            "message": message,
        }


personalized_offer_service = (
    PersonalizedOfferService()
)