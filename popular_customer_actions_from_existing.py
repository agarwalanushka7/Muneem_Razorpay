
import sqlite3
from pathlib import Path


# ============================================================
# MUNEEM — CREATE CUSTOMER ACTIONS FROM THE WORKING ACTION
# ============================================================
#
# This script intentionally uses SQLite directly.
# It does NOT import SQLAlchemy models.
#
# It uses the already-working Aarav Mehta action as the template
# for the action schema, then creates customer-specific actions
# for the other customers.
# ============================================================


def find_db():
    candidates = [
        Path("revenue_agent.db"),
        Path("src/backend/revenue_agent.db"),
        Path("backend/revenue_agent.db"),
    ]

    candidates += list(Path(".").rglob("revenue_agent.db"))

    seen = set()

    for p in candidates:
        p = p.resolve()

        if p in seen or not p.exists():
            continue

        seen.add(p)

        try:
            c = sqlite3.connect(str(p))
            tables = {
                r[0]
                for r in c.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            c.close()

            if {
                "customers",
                "products",
                "orders",
                "opportunities",
                "agent_actions",
            }.issubset(tables):
                return p
        except Exception:
            pass

    return None


def cols(conn, table):
    return {
        r[1]
        for r in conn.execute(
            f'PRAGMA table_info("{table}")'
        ).fetchall()
    }


def choose(c, names):
    for n in names:
        if n in c:
            return n
    return None


db_path = find_db()

if not db_path:
    raise RuntimeError(
        "Active revenue_agent.db was not found."
    )

print()
print("=" * 70)
print("MUNEEM — CUSTOMER ACTION BUILDER")
print("=" * 70)
print("Database:", db_path)
print()


conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

try:

    customer_cols = cols(conn, "customers")
    product_cols = cols(conn, "products")
    order_cols = cols(conn, "orders")
    opportunity_cols = cols(conn, "opportunities")
    action_cols = cols(conn, "agent_actions")

    # --------------------------------------------------------
    # Find a working action — preferably the Aarav/Gym Bottle
    # action that we know is rendering correctly.
    # --------------------------------------------------------

    template = None

    if {
        "customer_id",
        "product_id",
    }.issubset(action_cols):

        template = conn.execute(
            """
            SELECT *
            FROM agent_actions
            WHERE COALESCE(action_amount, 0) > 0
            ORDER BY id ASC
            LIMIT 1
            """
        ).fetchone()

    if not template:

        template = conn.execute(
            """
            SELECT *
            FROM agent_actions
            ORDER BY id ASC
            LIMIT 1
            """
        ).fetchone()

    if not template:
        raise RuntimeError(
            "No existing AgentAction found to use as a working template."
        )

    template_amount = 399.0

    for field in [
        "action_amount",
        "final_amount",
        "original_amount",
    ]:
        if field in action_cols:
            value = template[field]

            if value is not None and float(value or 0) > 0:
                template_amount = float(value)
                break

    print(
        "Working action template:",
        template["id"]
    )

    print(
        "Template amount: ₹",
        template_amount
    )

    # --------------------------------------------------------
    # Product prices
    # --------------------------------------------------------

    product_price = {}

    product_rows = conn.execute(
        "SELECT * FROM products"
    ).fetchall()

    for p in product_rows:

        price = (
            float(p["price"] or 0)
            if "price" in product_cols
            else 0
        )

        if price > 0:
            product_price[p["id"]] = price

    # --------------------------------------------------------
    # Infer prices from orders
    # --------------------------------------------------------

    order_amount = choose(
        order_cols,
        [
            "total_amount",
            "amount",
            "order_amount",
            "total",
            "price",
        ],
    )

    order_qty = choose(
        order_cols,
        [
            "quantity",
            "qty",
        ],
    )

    if order_amount:

        if order_qty:

            sql = f"""
                SELECT
                    product_id,
                    SUM(COALESCE("{order_amount}",0))
                        AS total_amount,
                    SUM(COALESCE("{order_qty}",1))
                        AS total_qty
                FROM orders
                WHERE product_id IS NOT NULL
                GROUP BY product_id
            """

        else:

            sql = f"""
                SELECT
                    product_id,
                    SUM(COALESCE("{order_amount}",0))
                        AS total_amount,
                    COUNT(*) AS total_qty
                FROM orders
                WHERE product_id IS NOT NULL
                GROUP BY product_id
            """

        for row in conn.execute(sql).fetchall():

            amount = float(
                row["total_amount"] or 0
            )

            quantity = float(
                row["total_qty"] or 0
            )

            if amount > 0 and quantity > 0:

                product_price[row["product_id"]] = (
                    amount / quantity
                )

    # --------------------------------------------------------
    # Existing agent actions are another reliable price source.
    # --------------------------------------------------------

    if "product_id" in action_cols:

        action_price_col = choose(
            action_cols,
            [
                "action_amount",
                "final_amount",
                "original_amount",
            ],
        )

        if action_price_col:

            rows = conn.execute(
                f"""
                SELECT product_id, "{action_price_col}" AS amount
                FROM agent_actions
                WHERE product_id IS NOT NULL
                  AND COALESCE("{action_price_col}",0) > 0
                """
            ).fetchall()

            for row in rows:

                product_price[row["product_id"]] = float(
                    row["amount"]
                )

    # --------------------------------------------------------
    # Customer purchase history
    # --------------------------------------------------------

    customer_products = {}

    for order in conn.execute(
        "SELECT customer_id, product_id FROM orders"
    ).fetchall():

        cid = order["customer_id"]
        pid = order["product_id"]

        if cid and pid:

            customer_products.setdefault(
                cid,
                set(),
            ).add(pid)

    customers = conn.execute(
        "SELECT * FROM customers"
    ).fetchall()

    products = conn.execute(
        "SELECT * FROM products"
    ).fetchall()

    # --------------------------------------------------------
    # Helper: product name
    # --------------------------------------------------------

    product_by_id = {
        p["id"]: p
        for p in products
    }

    # --------------------------------------------------------
    # Create customer-specific opportunities + actions.
    # --------------------------------------------------------

    created = 0

    for customer in customers:

        customer_id = customer["id"]

        bought = customer_products.get(
            customer_id,
            set(),
        )

        if not bought:
            continue

        # Choose a source product the customer actually bought.
        source_id = next(iter(bought))

        source = product_by_id.get(source_id)

        if not source:
            continue

        # Prefer a target that another existing action has already
        # proven to be a valid recommendation. Otherwise use a
        # product the customer has not bought.
        target = None

        if "product_id" in action_cols:

            existing_targets = conn.execute(
                """
                SELECT DISTINCT product_id
                FROM agent_actions
                WHERE product_id IS NOT NULL
                """
            ).fetchall()

            target_ids = [
                r["product_id"]
                for r in existing_targets
                if r["product_id"] not in bought
            ]

            if target_ids:
                target = product_by_id.get(
                    target_ids[0]
                )

        if not target:

            candidates = [
                p
                for p in products
                if p["id"] not in bought
            ]

            if not candidates:
                continue

            # Prefer a product with a known non-zero price.
            candidates.sort(
                key=lambda p: (
                    product_price.get(
                        p["id"],
                        0,
                    ) > 0,
                    product_price.get(
                        p["id"],
                        0,
                    ),
                ),
                reverse=True,
            )

            target = candidates[0]

        target_id = target["id"]

        # ----------------------------------------------------
        # Determine value.
        # ----------------------------------------------------

        price = product_price.get(
            target_id,
            0,
        )

        # If the target has no known price, use the working
        # action's proven amount as the fallback rather than
        # displaying ₹0. This is an ESTIMATED opportunity value.
        if price <= 0:
            price = template_amount

        customer_name = customer["name"]

        source_name = source["name"]

        target_name = target["name"]

        title = (
            f"{customer_name} may be ready for "
            f"{target_name}"
        )

        description = (
            f"{customer_name} recently purchased "
            f"{source_name}. MUNEEM identified "
            f"{target_name} as a relevant next purchase "
            f"based on the merchant's purchase history."
        )

        message = (
            f"MUNEEM recommends {target_name} "
            f"for {customer_name}."
        )

        # ----------------------------------------------------
        # Avoid duplicate customer + target action.
        # ----------------------------------------------------

        existing_action = None

        if {
            "customer_id",
            "product_id",
        }.issubset(action_cols):

            existing_action = conn.execute(
                """
                SELECT id
                FROM agent_actions
                WHERE customer_id = ?
                  AND product_id = ?
                LIMIT 1
                """,
                (
                    customer_id,
                    target_id,
                ),
            ).fetchone()

        if existing_action:
            continue

        # ----------------------------------------------------
        # Create opportunity.
        # ----------------------------------------------------

        opportunity_id = None

        if {
            "product_id",
            "related_product_id",
            "opportunity_type",
            "status",
        }.issubset(opportunity_cols):

            existing_opportunity = conn.execute(
                """
                SELECT id
                FROM opportunities
                WHERE opportunity_type = 'cross_sell'
                  AND product_id = ?
                  AND related_product_id = ?
                  AND status = 'open'
                LIMIT 1
                """,
                (
                    source_id,
                    target_id,
                ),
            ).fetchone()

            if existing_opportunity:
                opportunity_id = (
                    existing_opportunity["id"]
                )

            else:

                fields = [
                    "opportunity_type",
                    "product_id",
                    "related_product_id",
                    "title",
                    "description",
                    "customer_count",
                    "estimated_value",
                    "confidence",
                    "status",
                ]

                values = [
                    "cross_sell",
                    source_id,
                    target_id,
                    title,
                    description,
                    1,
                    price,
                    "High",
                    "open",
                ]

                available = [
                    f
                    for f in fields
                    if f in opportunity_cols
                ]

                vals = [
                    values[fields.index(f)]
                    for f in available
                ]

                placeholders = ", ".join(
                    ["?"] * len(available)
                )

                conn.execute(
                    f"""
                    INSERT INTO opportunities
                    ({", ".join(available)})
                    VALUES ({placeholders})
                    """,
                    vals,
                )

                opportunity_id = conn.execute(
                    "SELECT last_insert_rowid()"
                ).fetchone()[0]

                # Make the opportunity value explicit.
                if "estimated_value" in opportunity_cols:
                    conn.execute(
                        """
                        UPDATE opportunities
                        SET estimated_value = ?,
                            customer_count = 1
                        WHERE id = ?
                        """,
                        (
                            price,
                            opportunity_id,
                        ),
                    )

        if not opportunity_id:
            continue

        # ----------------------------------------------------
        # Create action with the SAME essential structure as
        # the working Aarav action.
        # ----------------------------------------------------

        action_fields = []
        action_values = []

        def add(field, value):
            if field in action_cols:
                action_fields.append(field)
                action_values.append(value)

        add(
            "opportunity_id",
            opportunity_id,
        )

        add(
            "customer_id",
            customer_id,
        )

        add(
            "product_id",
            target_id,
        )

        add(
            "action_type",
            "cross_sell",
        )

        add(
            "status",
            "pending_approval",
        )

        add(
            "approval_required",
            1,
        )

        add(
            "action_amount",
            price,
        )

        add(
            "original_amount",
            price,
        )

        add(
            "discount_percentage",
            0,
        )

        add(
            "discount_amount",
            0,
        )

        add(
            "final_amount",
            price,
        )

        add(
            "customer_message",
            message,
        )

        # ----------------------------------------------------
        # Timestamps
        # ----------------------------------------------------

        from datetime import datetime

        now = datetime.utcnow().isoformat()

        add(
            "created_at",
            now,
        )

        add(
            "updated_at",
            now,
        )

        placeholders = ", ".join(
            ["?"] * len(action_fields)
        )

        conn.execute(
            f"""
            INSERT INTO agent_actions
            ({", ".join(action_fields)})
            VALUES ({placeholders})
            """,
            action_values,
        )

        created += 1

        print(
            f"[{created}] {customer_name}"
        )

        print(
            f"    Bought: {source_name}"
        )

        print(
            f"    Recommended: {target_name}"
        )

        print(
            f"    Value: ₹{price:.0f}"
        )

        print(
            "    Status: pending approval"
        )

        print()

    conn.commit()

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    opportunities = conn.execute(
        "SELECT COUNT(*) FROM opportunities"
    ).fetchone()[0]

    actions = conn.execute(
        "SELECT COUNT(*) FROM agent_actions"
    ).fetchone()[0]

    print("=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print("New customer actions:", created)
    print("Total opportunities:", opportunities)
    print("Total agent actions:", actions)
    print("=" * 70)
    print()

finally:
    conn.close()
