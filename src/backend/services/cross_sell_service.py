from sqlalchemy.orm import Session

from src.backend.models.order import Order


class CrossSellService:

    def find_cross_sell_customers(
        self,
        db: Session,
        product_id: int,
        related_product_id: int,
    ):
        """
        Find customers who purchased the source product
        but have not purchased the recommended product.
        """

        # Customers who bought the source product
        source_customers = (
            db.query(Order.customer_id)
            .filter(
                Order.product_id == product_id
            )
            .distinct()
            .all()
        )

        source_customer_ids = [
            row[0]
            for row in source_customers
        ]

        if not source_customer_ids:
            return {
                "customer_ids": [],
                "count": 0,
            }

        # Customers who already bought the
        # recommended product
        existing_customers = (
            db.query(Order.customer_id)
            .filter(
                Order.product_id
                == related_product_id,
                Order.customer_id.in_(
                    source_customer_ids
                ),
            )
            .distinct()
            .all()
        )

        existing_customer_ids = {
            row[0]
            for row in existing_customers
        }

        # Remove customers who already own
        # the recommended product
        eligible_customer_ids = [
            customer_id
            for customer_id in source_customer_ids
            if customer_id
            not in existing_customer_ids
        ]

        return {
            "customer_ids": eligible_customer_ids,
            "count": len(
                eligible_customer_ids
            ),
        }


cross_sell_service = CrossSellService()


def find_cross_sell_customers(
    db: Session,
    product_id: int,
    related_product_id: int,
):
    return cross_sell_service.find_cross_sell_customers(
        db=db,
        product_id=product_id,
        related_product_id=related_product_id,
    )