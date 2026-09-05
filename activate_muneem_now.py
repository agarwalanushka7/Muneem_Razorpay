
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()

# Find the same database used by the existing Aarav activation script.
candidates = list(ROOT.rglob("revenue_agent.db"))

if not candidates:
    raise SystemExit(
        "ERROR: revenue_agent.db was not found. "
        "Run this from the Razorpay project root."
    )


def table_names(path):
    conn = sqlite3.connect(str(path))
    try:
        return {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        conn.close()


required_tables = {
    "customers",
    "products",
    "orders",
    "opportunities",
    "agent_actions",
}

db_path = None

for candidate in candidates:
    try:
        if required_tables.issubset(table_names(candidate)):
            db_path = candidate
            break
    except Exception:
        pass

if not db_path:
    raise SystemExit(
        "ERROR: A valid MUNEEM database was not found."
    )

print("Using database:", db_path)

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cur = conn.cursor()


def columns(table):
    return {
        row["name"]
        for row in cur.execute(
            f'PRAGMA table_info("{table}")'
        ).fetchall()
    }


def insert_dynamic(table, values):
    available = columns(table)

    data = {
        key: value
        for key, value in values.items()
        if key in available
    }

    if not data:
        raise RuntimeError(
            f"No compatible columns found for {table}"
        )

    names = ", ".join(
        f'"{key}"'
        for key in data
    )

    marks = ", ".join(
        "?"
        for _ in data
    )

    cur.execute(
        f'INSERT INTO "{table}" ({names}) VALUES ({marks})',
        list(data.values()),
    )

    return cur.lastrowid


def money(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


try:

    customers = cur.execute(
        "SELECT * FROM customers ORDER BY id"
    ).fetchall()

    products = cur.execute(
        "SELECT * FROM products ORDER BY id"
    ).fetchall()

    orders = cur.execute(
        "SELECT * FROM orders ORDER BY id"
    ).fetchall()

    print()
    print("=" * 70)
    print("MUNEEM — CUSTOMER RECOMMENDATION ACTIVATION")
    print("=" * 70)
    print("Customers:", len(customers))
    print("Products:", len(products))
    print("Orders:", len(orders))
    print("=" * 70)
    print()


    if not customers:
        raise SystemExit("No customers found.")

    if not products:
        raise SystemExit("No products found.")

    if not orders:
        raise SystemExit("No orders found.")


    # =====================================================
    # PRODUCT PRICES
    # =====================================================

    product_by_id = {
        product["id"]: product
        for product in products
    }

    product_prices = {}

    product_columns = columns("products")

    for product in products:

        if "price" in product_columns:
            price = money(product["price"])
        else:
            price = 0.0

        product_prices[
            product["id"]
        ] = price


    # Infer missing prices from real orders.

    order_columns = columns("orders")

    amount_column = None

    for name in [
        "total_amount",
        "amount",
        "order_amount",
        "total",
        "price",
    ]:

        if name in order_columns:
            amount_column = name
            break


    quantity_column = None

    for name in [
        "quantity",
        "qty",
    ]:

        if name in order_columns:
            quantity_column = name
            break


    if amount_column:

        if quantity_column:

            sql = (
                'SELECT product_id, '
                f'SUM(COALESCE("{amount_column}",0)) AS total_amount, '
                f'SUM(COALESCE("{quantity_column}",1)) AS total_quantity '
                'FROM orders '
                'WHERE product_id IS NOT NULL '
                'GROUP BY product_id'
            )

        else:

            sql = (
                'SELECT product_id, '
                f'SUM(COALESCE("{amount_column}",0)) AS total_amount, '
                'COUNT(*) AS total_quantity '
                'FROM orders '
                'WHERE product_id IS NOT NULL '
                'GROUP BY product_id'
            )

        for row in cur.execute(sql).fetchall():

            total_amount = money(
                row["total_amount"]
            )

            total_quantity = money(
                row["total_quantity"]
            )

            if (
                total_amount > 0
                and total_quantity > 0
            ):

                product_id = row[
                    "product_id"
                ]

                if product_prices.get(
                    product_id,
                    0,
                ) <= 0:

                    product_prices[
                        product_id
                    ] = (
                        total_amount
                        / total_quantity
                    )


    # The original Aarav action proves ₹399 is a valid
    # demo value in this merchant dataset. Use it only
    # where no real price exists.

    for product in products:

        if product_prices.get(
            product["id"],
            0,
        ) <= 0:

            product_prices[
                product["id"]
            ] = 399.0


    # =====================================================
    # CUSTOMER PURCHASE HISTORY
    # =====================================================

    customer_products = {}

    for order in orders:

        customer_id = order[
            "customer_id"
        ]

        product_id = order[
            "product_id"
        ]

        if not customer_id or not product_id:
            continue

        customer_products.setdefault(
            customer_id,
            set(),
        ).add(product_id)


    # =====================================================
    # PRODUCT -> CUSTOMERS
    # =====================================================

    product_customers = {}

    for customer_id, purchased in (
        customer_products.items()
    ):

        for product_id in purchased:

            product_customers.setdefault(
                product_id,
                set(),
            ).add(customer_id)


    opportunity_columns = columns(
        "opportunities"
    )

    action_columns = columns(
        "agent_actions"
    )


    # =====================================================
    # CREATE CUSTOMER-SPECIFIC ACTION
    # =====================================================

    def create_customer_action(
        customer,
        source_product,
        target_product,
    ):

        customer_id = customer["id"]

        source_id = source_product["id"]

        target_id = target_product["id"]

        customer_name = customer["name"]

        source_name = source_product["name"]

        target_name = target_product["name"]

        # Bounded merchant offer: 10% off for this recommendation.
        original_amount = product_prices.get(
            target_id,
            399.0,
        )

        if original_amount <= 0:
            original_amount = 399.0

        discount_percentage = 10
        discount_amount = round(
            original_amount * discount_percentage / 100,
            2,
        )
        final_amount = round(
            original_amount - discount_amount,
            2,
        )


        # -------------------------------------------------
        # Existing exact customer + target action?
        # -------------------------------------------------

        if {
            "customer_id",
            "product_id",
        }.issubset(action_columns):

            existing_action = cur.execute(
                "SELECT id FROM agent_actions "
                "WHERE customer_id = ? AND product_id = ? "
                "LIMIT 1",
                (
                    customer_id,
                    target_id,
                ),
            ).fetchone()

            if existing_action:

                update_fields = []
                update_values = []

                for field, value in [
                    ("action_amount", final_amount),
                    ("original_amount", original_amount),
                    ("final_amount", final_amount),
                    ("discount_percentage", discount_percentage),
                    ("discount_amount", discount_amount),
                ]:

                    if field in action_columns:

                        update_fields.append(
                            f'"{field}" = ?'
                        )

                        update_values.append(
                            value
                        )

                if update_fields:

                    update_values.append(
                        existing_action["id"]
                    )

                    cur.execute(
                        f'UPDATE agent_actions '
                        f'SET {", ".join(update_fields)} '
                        'WHERE id = ?',
                        update_values,
                    )

                return False


        # -------------------------------------------------
        # Reuse source -> target opportunity when possible.
        # -------------------------------------------------

        opportunity_id = None

        if {
            "product_id",
            "related_product_id",
            "opportunity_type",
            "status",
        }.issubset(opportunity_columns):

            existing_opportunity = cur.execute(
                "SELECT id FROM opportunities "
                "WHERE opportunity_type = 'cross_sell' "
                "AND product_id = ? "
                "AND related_product_id = ? "
                "AND status != 'rejected' "
                "ORDER BY id DESC LIMIT 1",
                (
                    source_id,
                    target_id,
                ),
            ).fetchone()

            if existing_opportunity:

                opportunity_id = (
                    existing_opportunity["id"]
                )


        title = (
            f"{customer_name} may be ready for "
            f"{target_name}"
        )

        description = (
            f"{customer_name} recently purchased "
            f"{source_name}. MUNEEM identified "
            f"{target_name} as a relevant next purchase "
            f"based on purchase behavior."
        )


        # -------------------------------------------------
        # Create opportunity.
        # -------------------------------------------------

        if opportunity_id is None:

            opportunity_id = insert_dynamic(
                "opportunities",
                {
                    "opportunity_type": "cross_sell",
                    "product_id": source_id,
                    "related_product_id": target_id,
                    "title": title,
                    "description": description,
                    "customer_count": 1,
                    "estimated_value": final_amount,
                    "confidence": "High",
                    "status": "open",
                    "created_at": datetime.utcnow().isoformat(),
                },
            )

        else:

            if "estimated_value" in opportunity_columns:

                cur.execute(
                    "UPDATE opportunities "
                    "SET estimated_value = ? "
                    "WHERE id = ?",
                    (
                        final_amount,
                        opportunity_id,
                    ),
                )


        # -------------------------------------------------
        # Create action — same essential structure as Aarav.
        # -------------------------------------------------

        action_values = {

            "opportunity_id":
                opportunity_id,

            "customer_id":
                customer_id,

            "product_id":
                target_id,

            "action_type":
                "cross_sell",

            "action_amount":
                final_amount,

            "original_amount":
                original_amount,

            "discount_percentage":
                discount_percentage,

            "discount_amount":
                discount_amount,

            "final_amount":
                final_amount,

            "customer_message":
                (
                    f"Hi {customer_name},\n\n"
                    f"Since you recently purchased "
                    f"{source_name}, we thought "
                    f"{target_name} would be a great "
                    f"addition for you.\n\n"
                    f"MUNEEM has unlocked a special "
                    f"{discount_percentage}% discount "
                    f"for you. Your price is now "
                    f"₹{final_amount:.0f}, down from "
                    f"₹{original_amount:.0f} — you save "
                    f"₹{discount_amount:.0f}.\n\n"
                    f"You can complete your purchase "
                    f"securely using the payment link "
                    f"below.\n\n"
                    f"Best,\n"
                    f"MUNEEM"
                ),

            "approval_required":
                1,

            "status":
                "pending_approval",

            "created_at":
                datetime.utcnow().isoformat(),

            "updated_at":
                datetime.utcnow().isoformat(),
        }


        action_id = insert_dynamic(
            "agent_actions",
            action_values,
        )


        print(
            f"[ACTION #{action_id}] "
            f"{customer_name}"
        )

        print(
            f"    Bought: {source_name}"
        )

        print(
            f"    Recommended: {target_name}"
        )

        print(
            f"    Original: ₹{original_amount:.0f}"
        )

        print(
            f"    Discount: {discount_percentage}% "
            f"(₹{discount_amount:.0f} saved)"
        )

        print(
            f"    Customer pays: ₹{final_amount:.0f}"
        )

        print(
            "    Status: pending approval"
        )

        print()

        return True


    # =====================================================
    # GENERATE ONE ACTION FOR EACH CUSTOMER
    # =====================================================

    created = 0

    skipped = 0


    for customer in customers:

        customer_id = customer["id"]

        bought = customer_products.get(
            customer_id,
            set(),
        )

        if not bought:

            print(
                f"Skipping {customer['name']} "
                "(no purchase history)"
            )

            skipped += 1

            continue


        # Score unpurchased products by actual behavior:
        # what did OTHER customers buy after/alongside
        # products this customer already bought?

        candidate_scores = {}


        for source_id in bought:

            other_customers = (
                product_customers.get(
                    source_id,
                    set(),
                )
            )

            for other_customer_id in (
                other_customers
            ):

                if (
                    other_customer_id
                    == customer_id
                ):
                    continue

                other_bought = (
                    customer_products.get(
                        other_customer_id,
                        set(),
                    )
                )

                for target_id in other_bought:

                    if target_id in bought:
                        continue

                    candidate_scores[
                        target_id
                    ] = (
                        candidate_scores.get(
                            target_id,
                            0,
                        )
                        + 1
                    )


        if candidate_scores:

            ranked = sorted(
                candidate_scores.items(),
                key=lambda item: (
                    item[1],
                    product_prices.get(
                        item[0],
                        0,
                    ),
                ),
                reverse=True,
            )

            target_id = ranked[0][0]

        else:

            candidates_for_customer = [
                product
                for product in products
                if product["id"] not in bought
            ]

            if not candidates_for_customer:

                skipped += 1
                continue

            candidates_for_customer.sort(
                key=lambda product: (
                    product_prices.get(
                        product["id"],
                        0,
                    ),
                    product["id"],
                ),
                reverse=True,
            )

            target_id = (
                candidates_for_customer[0]["id"]
            )


        source_id = next(
            iter(bought)
        )


        source_product = product_by_id[
            source_id
        ]

        target_product = product_by_id[
            target_id
        ]


        if create_customer_action(
            customer,
            source_product,
            target_product,
        ):

            created += 1


    conn.commit()


    # =====================================================
    # FINAL VERIFICATION
    # =====================================================

    opportunity_count = cur.execute(
        "SELECT COUNT(*) FROM opportunities"
    ).fetchone()[0]

    action_count = cur.execute(
        "SELECT COUNT(*) FROM agent_actions"
    ).fetchone()[0]


    positive_actions = 0

    value_column = None

    for field in [
        "action_amount",
        "final_amount",
        "original_amount",
    ]:

        if field in action_columns:

            value_column = field
            break


    if value_column:

        positive_actions = cur.execute(
            f'SELECT COUNT(*) FROM agent_actions '
            f'WHERE COALESCE("{value_column}", 0) > 0'
        ).fetchone()[0]


    print()
    print("=" * 70)
    print("MUNEEM CUSTOMER RECOMMENDATIONS COMPLETE")
    print("=" * 70)
    print("New customer actions:", created)
    print("Skipped customers:", skipped)
    print("Total opportunities:", opportunity_count)
    print("Total agent actions:", action_count)
    print(
        "Actions with positive value:",
        positive_actions,
    )
    print("=" * 70)
    print()


finally:

    conn.close()
