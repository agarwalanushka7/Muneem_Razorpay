from sqlalchemy.orm import Session

from src.backend.models.customer import Customer
from src.backend.models.product import Product
from src.backend.models.order import Order
from src.backend.models.opportunity import Opportunity
from src.backend.models.agent_action import AgentAction


def _model_fields(model):
    """Return the database column names for a SQLAlchemy model."""
    return {
        column.name
        for column in model.__table__.columns
    }


def _set_if_exists(obj, field, value):
    """Set a model field only when that column exists."""
    if field in _model_fields(type(obj)):
        setattr(obj, field, value)


# =========================================================
# DATA-BACKED OFFER DECISION
# =========================================================

def _recommended_discount(
    customer_orders,
    customer_total_spend,
):
    """
    Determine the discount recommended by MUNEEM
    from the customer's purchase behaviour.

    Maximum discount is always 10%.
    """

    order_count = len(customer_orders)
    total_spend = float(
        customer_total_spend or 0
    )

    # -----------------------------------------------------
    # BASE DISCOUNT FROM PURCHASE FREQUENCY
    # -----------------------------------------------------

    if order_count >= 4:
        discount = 10.0

    elif order_count >= 2:
        discount = 7.0

    else:
        discount = 5.0

    # -----------------------------------------------------
    # HIGH-VALUE CUSTOMER SIGNAL
    # -----------------------------------------------------
    # A customer with meaningful total spend gets a
    # stronger incentive, while remaining within the
    # merchant's 10% maximum.
    # -----------------------------------------------------

    if total_spend >= 10000:
        discount = max(
            discount,
            10.0,
        )

    elif total_spend >= 5000:
        discount = max(
            discount,
            7.0,
        )

    return min(
        10.0,
        max(
            0.0,
            discount,
        ),
    )


def _build_customer_message(
    customer_name,
    source_product_name,
    target_product_name,
    original_amount,
    discount_percentage,
    discount_amount,
    final_amount,
):
    """
    Build the personalized offer message stored on
    the AgentAction.

    Razorpay adds the payment link later when the
    merchant approves the offer.
    """

    if discount_percentage > 0:

        offer_line = (
            f"MUNEEM has unlocked a special "
            f"{discount_percentage:g}% discount for you. "
            f"Your personalized price is "
            f"₹{final_amount:,.2f}, down from "
            f"₹{original_amount:,.2f}. "
            f"You save ₹{discount_amount:,.2f}."
        )

    else:

        offer_line = (
            f"Your personalized price for "
            f"{target_product_name} is "
            f"₹{final_amount:,.2f}."
        )

    return (
        f"Hi {customer_name},\n\n"
        f"We noticed your recent purchase of "
        f"{source_product_name} and thought "
        f"{target_product_name} would be a great "
        f"addition to what you've already picked up.\n\n"
        f"{offer_line}\n\n"
        f"You can complete your purchase securely "
        f"using the payment link below.\n\n"
        f"Best,\n"
        f"MUNEEM"
    )


def run_revenue_agent(
    db: Session,
    upload_context: dict | None = None,
):
    """
    Read merchant data and create data-backed revenue
    opportunities and agent actions.

    The agent determines the recommended discount from
    customer purchase behaviour.

    When called immediately after a CSV/Excel confirmation,
    upload_context contains the exact parsed upload. The agent
    uses that context to scope the analysis to the merchant's
    current upload while SQLite remains the persistent source
    of truth.

    This service does not read files from disk and does not
    touch Razorpay.
    """

    customers = db.query(Customer).all()
    products = db.query(Product).all()
    orders = db.query(Order).all()

    if not customers or not products or not orders:
        return {
            "status": "skipped",
            "reason": "Not enough customer, product, or order data",
            "customers_analyzed": len(customers),
            "products_analyzed": len(products),
            "orders_analyzed": len(orders),
            "opportunities_created": 0,
            "actions_created": 0,
            "upload_used": bool(upload_context),
        }

    # =========================================================
    # CURRENT UPLOAD -> DATABASE RECORDS
    # =========================================================

    upload_customer_names = set()
    upload_customer_emails = set()
    upload_product_names = set()

    if isinstance(upload_context, dict):

        mappings = upload_context.get(
            "mappings",
            [],
        )

        rows = upload_context.get(
            "rows",
            [],
        )

        source_to_target = {}

        for mapping in mappings:

            if not isinstance(mapping, dict):
                continue

            source = mapping.get(
                "source_column"
            )

            target = mapping.get(
                "target_field"
            )

            if (
                source
                and target
                and target != "ignore"
            ):

                source_to_target[
                    str(source)
                ] = str(target)

        def clean(value):

            if value is None:
                return ""

            try:

                # NaN != NaN
                if value != value:
                    return ""

            except Exception:
                pass

            return str(value).strip()

        for row in rows:

            if not isinstance(row, dict):
                continue

            for source, value in row.items():

                target = source_to_target.get(
                    str(source)
                )

                value = clean(value)

                if not value:
                    continue

                target = (
                    target.strip().lower()
                    if target
                    else ""
                )

                if target in {
                    "customer_name",
                    "order_customer",
                }:

                    upload_customer_names.add(
                        value.lower()
                    )

                elif target == "customer_email":

                    upload_customer_emails.add(
                        value.lower()
                    )

                elif target in {
                    "product_name",
                    "order_product",
                }:

                    upload_product_names.add(
                        value.lower()
                    )

    # =========================================================
    # MATCH UPLOAD RECORDS TO PERSISTED RECORDS
    # =========================================================

    scoped_customer_ids = set()

    if (
        upload_customer_names
        or upload_customer_emails
    ):

        for customer in customers:

            name = str(
                getattr(
                    customer,
                    "name",
                    "",
                )
                or ""
            ).strip().lower()

            email = str(
                getattr(
                    customer,
                    "email",
                    "",
                )
                or ""
            ).strip().lower()

            if (
                name in upload_customer_names
                or email in upload_customer_emails
            ):

                scoped_customer_ids.add(
                    customer.id
                )

    scoped_product_ids = set()

    if upload_product_names:

        for product in products:

            name = str(
                getattr(
                    product,
                    "name",
                    "",
                )
                or ""
            ).strip().lower()

            if name in upload_product_names:

                scoped_product_ids.add(
                    product.id
                )

    # =========================================================
    # FALLBACK TO DATABASE-WIDE ANALYSIS
    # =========================================================

    if not scoped_customer_ids:

        scoped_customer_ids = {
            customer.id
            for customer in customers
            if getattr(
                customer,
                "id",
                None,
            ) is not None
        }

    if not scoped_product_ids:

        scoped_product_ids = {
            product.id
            for product in products
            if getattr(
                product,
                "id",
                None,
            ) is not None
        }

    scoped_customers = [
        customer
        for customer in customers
        if customer.id in scoped_customer_ids
    ]

    scoped_products = [
        product
        for product in products
        if product.id in scoped_product_ids
    ]

    scoped_orders = [
        order
        for order in orders
        if (
            getattr(
                order,
                "customer_id",
                None,
            ) in scoped_customer_ids

            and getattr(
                order,
                "product_id",
                None,
            ) in scoped_product_ids
        )
    ]

    # =========================================================
    # SAFETY FALLBACK
    # =========================================================

    if not scoped_orders:

        scoped_customers = customers
        scoped_products = products
        scoped_orders = orders

    # =========================================================
    # CUSTOMER -> PURCHASED PRODUCTS
    # =========================================================

    customer_products = {}

    for order in scoped_orders:

        customer_id = getattr(
            order,
            "customer_id",
            None,
        )

        product_id = getattr(
            order,
            "product_id",
            None,
        )

        if not customer_id or not product_id:
            continue

        customer_products.setdefault(
            customer_id,
            set(),
        ).add(product_id)

    if not customer_products:

        return {
            "status": "skipped",
            "reason": (
                "No usable customer-product "
                "order relationships"
            ),
            "customers_analyzed":
                len(scoped_customers),
            "products_analyzed":
                len(scoped_products),
            "orders_analyzed":
                len(scoped_orders),
            "opportunities_created": 0,
            "actions_created": 0,
            "upload_used":
                bool(upload_context),
        }

    # =========================================================
    # CUSTOMER LOOKUP
    # =========================================================

    customer_lookup = {
        customer.id: customer
        for customer in scoped_customers
    }

    # =========================================================
    # CROSS-SELL OPPORTUNITIES
    # =========================================================

    opportunities_created = 0
    actions_created = 0
    existing_actions = 0

    for source_product in scoped_products:

        source_buyers = [
            customer_id
            for customer_id, purchased
            in customer_products.items()
            if source_product.id in purchased
        ]

        if not source_buyers:
            continue

        for target_product in scoped_products:

            if (
                target_product.id
                == source_product.id
            ):
                continue

            target_customer_ids = [
                customer_id
                for customer_id in source_buyers
                if target_product.id
                not in customer_products.get(
                    customer_id,
                    set(),
                )
            ]

            if not target_customer_ids:
                continue

            target_price = float(
                getattr(
                    target_product,
                    "price",
                    0,
                )
                or 0
            )

            if target_price <= 0:
                continue

            estimated_value = (
                target_price
                * len(target_customer_ids)
            )

            # =================================================
            # EXISTING OPPORTUNITY
            # =================================================

            existing = (
                db.query(Opportunity)
                .filter(
                    Opportunity.product_id
                    == source_product.id,

                    Opportunity.related_product_id
                    == target_product.id,

                    Opportunity.status
                    == "open",
                )
                .first()
            )

            if existing:

                opportunity = existing

                _set_if_exists(
                    opportunity,
                    "customer_count",
                    len(target_customer_ids),
                )

                _set_if_exists(
                    opportunity,
                    "estimated_value",
                    estimated_value,
                )

            else:

                opportunity = Opportunity()

                _set_if_exists(
                    opportunity,
                    "opportunity_type",
                    "cross_sell",
                )

                _set_if_exists(
                    opportunity,
                    "product_id",
                    source_product.id,
                )

                _set_if_exists(
                    opportunity,
                    "related_product_id",
                    target_product.id,
                )

                _set_if_exists(
                    opportunity,
                    "title",
                    (
                        f"Cross-sell "
                        f"{target_product.name} "
                        f"to "
                        f"{len(target_customer_ids)} "
                        f"customers"
                    ),
                )

                _set_if_exists(
                    opportunity,
                    "description",
                    (
                        f"Customers who purchased "
                        f"{source_product.name} have not "
                        f"purchased "
                        f"{target_product.name}. "
                        f"MUNEEM identified "
                        f"{len(target_customer_ids)} "
                        f"potential customers from the "
                        f"merchant's uploaded data."
                    ),
                )

                _set_if_exists(
                    opportunity,
                    "customer_count",
                    len(target_customer_ids),
                )

                _set_if_exists(
                    opportunity,
                    "estimated_value",
                    estimated_value,
                )

                _set_if_exists(
                    opportunity,
                    "confidence",
                    "High",
                )

                _set_if_exists(
                    opportunity,
                    "status",
                    "open",
                )

                db.add(opportunity)

                db.flush()

                opportunities_created += 1

            # =================================================
            # CREATE / UPDATE AGENT ACTIONS
            # =================================================

            for customer_id in target_customer_ids:

                customer = customer_lookup.get(
                    customer_id
                )

                if not customer:
                    continue

                # -------------------------------------------------
                # CUSTOMER-SPECIFIC PURCHASE DATA
                # -------------------------------------------------

                customer_orders = [
                    order
                    for order in scoped_orders
                    if getattr(
                        order,
                        "customer_id",
                        None,
                    ) == customer_id
                ]

                customer_total_spend = 0.0

                for order in customer_orders:

                    amount = getattr(
                        order,
                        "total_amount",
                        None,
                    )

                    if amount is None:

                        amount = getattr(
                            order,
                            "amount",
                            0,
                        )

                    try:

                        customer_total_spend += float(
                            amount or 0
                        )

                    except (
                        ValueError,
                        TypeError,
                    ):

                        pass

                # -------------------------------------------------
                # MUNEEM RECOMMENDS DISCOUNT
                # -------------------------------------------------

                discount_percentage = (
                    _recommended_discount(
                        customer_orders,
                        customer_total_spend,
                    )
                )

                discount_amount = round(
                    target_price
                    * discount_percentage
                    / 100,
                    2,
                )

                final_amount = round(
                    target_price
                    - discount_amount,
                    2,
                )

                customer_message = (
                    _build_customer_message(
                        customer_name=customer.name,
                        source_product_name=(
                            source_product.name
                        ),
                        target_product_name=(
                            target_product.name
                        ),
                        original_amount=(
                            target_price
                        ),
                        discount_percentage=(
                            discount_percentage
                        ),
                        discount_amount=(
                            discount_amount
                        ),
                        final_amount=(
                            final_amount
                        ),
                    )
                )

                # -------------------------------------------------
                # CHECK EXISTING ACTION FOR THIS CUSTOMER
                # -------------------------------------------------

                existing_action = (
                    db.query(AgentAction)
                    .filter(
                        AgentAction.opportunity_id
                        == opportunity.id,

                        AgentAction.customer_id
                        == customer_id,
                    )
                    .first()
                )

                if existing_action:

                    existing_actions += 1

                    # ---------------------------------------------
                    # Repair/update old pending actions that may
                    # have been created with a 0% discount.
                    #
                    # Never overwrite approved/executed actions.
                    # ---------------------------------------------

                    existing_status = str(
                        getattr(
                            existing_action,
                            "status",
                            "",
                        )
                        or ""
                    ).lower()

                    if existing_status in {
                        "pending",
                        "pending_approval",
                    }:

                        _set_if_exists(
                            existing_action,
                            "action_amount",
                            final_amount,
                        )

                        _set_if_exists(
                            existing_action,
                            "original_amount",
                            target_price,
                        )

                        _set_if_exists(
                            existing_action,
                            "discount_percentage",
                            discount_percentage,
                        )

                        _set_if_exists(
                            existing_action,
                            "discount_amount",
                            discount_amount,
                        )

                        _set_if_exists(
                            existing_action,
                            "final_amount",
                            final_amount,
                        )

                        _set_if_exists(
                            existing_action,
                            "customer_message",
                            customer_message,
                        )

                        _set_if_exists(
                            existing_action,
                            "approval_required",
                            True,
                        )

                        _set_if_exists(
                            existing_action,
                            "status",
                            "pending_approval",
                        )

                    # We already have an action for this
                    # customer/opportunity.
                    continue

                # -------------------------------------------------
                # CREATE NEW AGENT ACTION
                # -------------------------------------------------

                action = AgentAction()

                _set_if_exists(
                    action,
                    "opportunity_id",
                    opportunity.id,
                )

                _set_if_exists(
                    action,
                    "customer_id",
                    customer_id,
                )

                _set_if_exists(
                    action,
                    "product_id",
                    target_product.id,
                )

                _set_if_exists(
                    action,
                    "action_type",
                    "cross_sell",
                )

                _set_if_exists(
                    action,
                    "status",
                    "pending_approval",
                )

                _set_if_exists(
                    action,
                    "approval_required",
                    True,
                )

                _set_if_exists(
                    action,
                    "action_amount",
                    final_amount,
                )

                _set_if_exists(
                    action,
                    "original_amount",
                    target_price,
                )

                # =================================================
                # THIS IS NOW THE AGENT'S RECOMMENDED DISCOUNT
                # =================================================

                _set_if_exists(
                    action,
                    "discount_percentage",
                    discount_percentage,
                )

                _set_if_exists(
                    action,
                    "discount_amount",
                    discount_amount,
                )

                _set_if_exists(
                    action,
                    "final_amount",
                    final_amount,
                )

                _set_if_exists(
                    action,
                    "customer_message",
                    customer_message,
                )

                db.add(action)

                actions_created += 1

            # Don't flood the merchant dashboard.

            if opportunities_created >= 8:
                break

        if opportunities_created >= 8:
            break

    db.commit()

    return {
        "status": "completed",

        "customers_analyzed":
            len(scoped_customers),

        "products_analyzed":
            len(scoped_products),

        "orders_analyzed":
            len(scoped_orders),

        "opportunities_created":
            opportunities_created,

        "actions_created":
            actions_created,

        "existing_actions":
            existing_actions,

        "upload_used":
            bool(upload_context),

        "upload_filename": (
            upload_context.get("filename")
            if isinstance(
                upload_context,
                dict,
            )
            else None
        ),

        "upload_rows_analyzed": (
            upload_context.get(
                "row_count",
                0,
            )
            if isinstance(
                upload_context,
                dict,
            )
            else 0
        ),
    }