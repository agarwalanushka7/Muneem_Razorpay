from collections import defaultdict

from sqlalchemy.orm import Session

from src.backend.models.opportunity import Opportunity
from src.backend.models.order import Order
from src.backend.models.product import Product


def detect_cross_sell_opportunities(
    db: Session,
):
    # =====================================================
    # GET ORDERS
    # =====================================================

    orders = (
        db.query(Order)
        .all()
    )

    if not orders:
        return []

    # =====================================================
    # BUILD CUSTOMER → PRODUCTS MAP
    #
    # Example:
    #
    # customer 1 → {Running Shoes, Sports Socks}
    # customer 2 → {Running Shoes}
    # customer 3 → {Running Shoes}
    # =====================================================

    customer_products = defaultdict(set)

    for order in orders:

        if (
            order.customer_id is None
            or order.product_id is None
        ):
            continue

        customer_products[
            order.customer_id
        ].add(
            order.product_id
        )

    if not customer_products:
        return []

    # =====================================================
    # BUILD PRODUCT → CUSTOMERS MAP
    #
    # Example:
    #
    # Running Shoes → {1, 2, 3}
    # Sports Socks  → {1}
    # =====================================================

    product_customers = defaultdict(set)

    for (
        customer_id,
        product_ids,
    ) in customer_products.items():

        for product_id in product_ids:

            product_customers[
                product_id
            ].add(
                customer_id
            )

    # =====================================================
    # LOAD PRODUCTS
    # =====================================================

    products = (
        db.query(Product)
        .all()
    )

    product_map = {
        product.id: product
        for product in products
    }

    opportunities = []

    # =====================================================
    # FIND CROSS-SELL OPPORTUNITIES
    # =====================================================

    for (
        source_product_id,
        source_customer_ids,
    ) in product_customers.items():

        # Need at least two customers buying
        # the source product before calling it
        # a meaningful segment.
        if len(source_customer_ids) < 2:
            continue

        source_product = product_map.get(
            source_product_id
        )

        if not source_product:
            continue

        for (
            related_product_id,
            related_product,
        ) in product_map.items():

            # Don't recommend the product
            # that the customer already bought.
            if (
                related_product_id
                == source_product_id
            ):
                continue

            related_customer_ids = (
                product_customers.get(
                    related_product_id,
                    set(),
                )
            )

            # Customers who bought BOTH products.
            overlap_customers = (
                source_customer_ids
                & related_customer_ids
            )

            # Customers who bought source
            # but haven't bought related product.
            missing_customers = (
                source_customer_ids
                - related_customer_ids
            )

            # We need evidence that at least
            # one customer bought both products.
            if not overlap_customers:
                continue

            # There must actually be customers
            # who could be targeted.
            if not missing_customers:
                continue

            # =================================================
            # CONFIDENCE
            # =================================================

            source_count = len(
                source_customer_ids
            )

            overlap_count = len(
                overlap_customers
            )

            overlap_ratio = (
                overlap_count
                / source_count
            )

            if overlap_ratio >= 0.5:
                confidence = "High"

            elif overlap_ratio >= 0.25:
                confidence = "Medium"

            else:
                confidence = "Low"

            # =================================================
            # ESTIMATED VALUE
            # =================================================

            related_price = (
                related_product.price
                or 0.0
            )

            estimated_value = (
                len(missing_customers)
                * related_price
            )

            # Don't create meaningless
            # zero-value opportunities.
            if estimated_value <= 0:
                continue

            # =================================================
            # CHECK FOR EXISTING OPPORTUNITY
            # =================================================

            existing = (
                db.query(Opportunity)
                .filter(
                    Opportunity.opportunity_type
                    == "cross_sell",

                    Opportunity.product_id
                    == source_product_id,

                    Opportunity.related_product_id
                    == related_product_id,

                    Opportunity.status
                    != "closed",
                )
                .first()
            )

            # =================================================
            # UPDATE EXISTING OPPORTUNITY
            # =================================================

            if existing:

                existing.customer_count = (
                    len(missing_customers)
                )

                existing.estimated_value = (
                    estimated_value
                )

                existing.confidence = (
                    confidence
                )

                existing.description = (
                    f"{len(missing_customers)} "
                    f"customers purchased "
                    f"{source_product.name} "
                    f"but did not purchase "
                    f"{related_product.name}. "
                    f"{overlap_count} customers "
                    f"purchased both products, "
                    f"indicating a potential "
                    f"cross-sell relationship."
                )

                opportunities.append(
                    existing
                )

                continue

            # =================================================
            # CREATE NEW OPPORTUNITY
            # =================================================

            opportunity = Opportunity(
                opportunity_type="cross_sell",

                title=(
                    "Cross-sell opportunity: "
                    f"{related_product.name}"
                ),

                description=(
                    f"{len(missing_customers)} "
                    f"customers purchased "
                    f"{source_product.name} "
                    f"but did not purchase "
                    f"{related_product.name}. "
                    f"{overlap_count} customers "
                    f"purchased both products, "
                    f"indicating a potential "
                    f"cross-sell relationship."
                ),

                product_id=source_product_id,

                related_product_id=(
                    related_product_id
                ),

                customer_count=(
                    len(missing_customers)
                ),

                estimated_value=(
                    estimated_value
                ),

                confidence=confidence,

                status="new",
            )

            db.add(opportunity)

            opportunities.append(
                opportunity
            )

    # =====================================================
    # SAVE
    # =====================================================

    db.commit()

    # =====================================================
    # REFRESH
    # =====================================================

    for opportunity in opportunities:

        db.refresh(opportunity)

    return opportunities