
from pathlib import Path
import sys
from datetime import datetime

# Run this from the Razorpay project root.
ROOT = Path.cwd()
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(ROOT))

from src.backend.database import SessionLocal
from src.backend.models.customer import Customer
from src.backend.models.product import Product
from src.backend.models.order import Order
from src.backend.models.opportunity import Opportunity
from src.backend.models.agent_action import AgentAction

db = SessionLocal()

def fields(model):
    return {c.name for c in model.__table__.columns}

def set_if(obj, name, value):
    if name in fields(type(obj)):
        setattr(obj, name, value)

try:
    customers = db.query(Customer).all()
    products = db.query(Product).all()
    orders = db.query(Order).all()

    print("Customers:", len(customers))
    print("Products:", len(products))
    print("Orders:", len(orders))

    if not customers:
        raise RuntimeError("No customers exist. Import the customer CSV first.")

    if len(products) < 2:
        raise RuntimeError(
            "MUNEEM needs at least 2 products for a cross-sell action. "
            "Import a product/order Excel or CSV containing another product."
        )

    # Pick a real customer and two real products.
    customer = customers[0]
    source_product = products[0]
    target_product = products[1]

    # If an order exists, use its real customer/product.
    if orders:
        source_product = next(
            (p for p in products if p.id == orders[0].product_id),
            source_product,
        )
        customer = next(
            (c for c in customers if c.id == orders[0].customer_id),
            customer,
        )

        target_product = next(
            (p for p in products if p.id != source_product.id),
            products[1],
        )

    amount = float(target_product.price or 399)

    # ---------------------------------------------------------
    # Opportunity
    # ---------------------------------------------------------
    opportunity = (
        db.query(Opportunity)
        .filter(
            Opportunity.status != "rejected"
        )
        .order_by(Opportunity.id.desc())
        .first()
    )

    if not opportunity:
        opportunity = Opportunity()

        set_if(opportunity, "opportunity_type", "cross_sell")
        set_if(opportunity, "product_id", source_product.id)
        set_if(opportunity, "related_product_id", target_product.id)
        set_if(
            opportunity,
            "title",
            f"Cross-sell {target_product.name} to {customer.name}",
        )
        set_if(
            opportunity,
            "description",
            (
                f"{customer.name} has purchase history with "
                f"{source_product.name}. MUNEEM recommends "
                f"{target_product.name} as the next revenue opportunity."
            ),
        )
        set_if(opportunity, "customer_count", 1)
        set_if(opportunity, "estimated_value", amount)
        set_if(opportunity, "confidence", "High")
        set_if(opportunity, "status", "open")
        set_if(opportunity, "created_at", datetime.utcnow())

        db.add(opportunity)
        db.flush()

        print("Created Opportunity:", opportunity.id)
    else:
        # Make an existing opportunity visibly actionable.
        set_if(opportunity, "status", "open")
        set_if(opportunity, "estimated_value", amount)
        db.flush()
        print("Using Opportunity:", opportunity.id)

    # ---------------------------------------------------------
    # Agent Action
    # ---------------------------------------------------------
    action = (
        db.query(AgentAction)
        .filter(
            AgentAction.opportunity_id == opportunity.id
        )
        .order_by(AgentAction.id.desc())
        .first()
    )

    if not action:
        action = AgentAction()

        set_if(action, "opportunity_id", opportunity.id)
        set_if(action, "customer_id", customer.id)
        set_if(action, "product_id", target_product.id)

        set_if(action, "action_type", "cross_sell")
        set_if(action, "action_amount", amount)
        set_if(action, "original_amount", amount)
        set_if(action, "discount_percentage", 0)
        set_if(action, "discount_amount", 0)
        set_if(action, "final_amount", amount)

        set_if(
            action,
            "customer_message",
            (
                f"MUNEEM recommends {target_product.name} "
                f"for {customer.name}."
            ),
        )

        set_if(action, "approval_required", 1)
        set_if(action, "status", "pending_approval")
        set_if(action, "created_at", datetime.utcnow())
        set_if(action, "updated_at", datetime.utcnow())

        db.add(action)
        db.flush()

        print("Created Agent Action:", action.id)
    else:
        set_if(action, "status", "pending_approval")
        set_if(action, "approval_required", 1)
        db.flush()
        print("Using Agent Action:", action.id)

    db.commit()

    # Final verification.
    opp_count = db.query(Opportunity).count()
    action_count = db.query(AgentAction).count()

    print()
    print("========================================")
    print("MUNEEM AGENT ACTIVATION COMPLETE")
    print("========================================")
    print("Opportunities:", opp_count)
    print("Agent Actions:", action_count)
    print("Opportunity ID:", opportunity.id)
    print("Action ID:", action.id)
    print("Action Status:", getattr(action, "status", None))
    print("Action Amount:", getattr(action, "action_amount", None))
    print("========================================")
    print()
    print("NOW refresh the Revenue and Agent Actions pages.")

except Exception as e:
    db.rollback()
    print()
    print("MUNEEM ACTIVATION FAILED")
    print(type(e).__name__ + ":", str(e))
    print()
    raise
finally:
    db.close()
