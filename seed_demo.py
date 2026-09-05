from datetime import datetime

from src.backend.database import Base, SessionLocal, engine

from src.backend.models.customer import Customer
from src.backend.models.product import Product
from src.backend.models.order import Order
from src.backend.models.transaction import Transaction
from src.backend.models.opportunity import Opportunity
from src.backend.models.agent_action import AgentAction


# =========================================================
# RESET DATABASE
# =========================================================

def reset_database():
    print("Resetting MUNEEM demo database...")

    # Delete dependent records first.
    # This prevents foreign-key problems.
    db = SessionLocal()

    try:
        db.query(Transaction).delete()
        db.query(AgentAction).delete()
        db.query(Order).delete()
        db.query(Opportunity).delete()
        db.query(Customer).delete()
        db.query(Product).delete()

        db.commit()

        print("Old demo data removed.")

    finally:
        db.close()


# =========================================================
# SEED DEMO DATA
# =========================================================

def seed_demo_data():

    db = SessionLocal()

    try:

        # =====================================================
        # PRODUCTS
        # =====================================================

        products = [
            Product(
                id=101,
                name="Running Shoes",
                description=(
                    "Performance running shoes "
                    "for everyday training."
                ),
                price=2499.0,
                inventory=50,
                category="Footwear",
            ),

            Product(
                id=102,
                name="Sports Socks",
                description=(
                    "Breathable sports socks "
                    "for running and training."
                ),
                price=399.0,
                inventory=100,
                category="Accessories",
            ),

            Product(
                id=103,
                name="Gym Bottle",
                description=(
                    "Reusable insulated gym bottle."
                ),
                price=699.0,
                inventory=75,
                category="Accessories",
            ),

            Product(
                id=104,
                name="Training Gloves",
                description=(
                    "Grip-enhancing gloves "
                    "for strength training."
                ),
                price=899.0,
                inventory=60,
                category="Training",
            ),

            Product(
                id=105,
                name="Gym Bag",
                description=(
                    "Compact everyday training bag."
                ),
                price=1499.0,
                inventory=40,
                category="Accessories",
            ),
        ]

        db.add_all(products)

        # =====================================================
        # CUSTOMERS
        # =====================================================

        customers = [
            Customer(
                id=201,
                name="Aarav",
                email="aarav@muneem.demo",
                phone="+919900000201",
                total_orders=1,
                total_spent=399.0,
            ),

            Customer(
                id=202,
                name="Priya",
                email="priya@muneem.demo",
                phone="+919900000202",
                total_orders=2,
                total_spent=3198.0,
            ),

            Customer(
                id=203,
                name="Rohan",
                email="rohan@muneem.demo",
                phone="+919900000203",
                total_orders=2,
                total_spent=1098.0,
            ),

            Customer(
                id=204,
                name="Ananya",
                email="ananya@muneem.demo",
                phone="+919900000204",
                total_orders=2,
                total_spent=1298.0,
            ),

            Customer(
                id=205,
                name="Kabir",
                email="kabir@muneem.demo",
                phone="+919900000205",
                total_orders=2,
                total_spent=2898.0,
            ),
        ]

        db.add_all(customers)

        db.flush()

        # =====================================================
        # ORDERS
        # =====================================================

        orders = [

            # -------------------------------------------------
            # AARAV
            # Sports Socks → Running Shoes opportunity
            # -------------------------------------------------

            Order(
                id=301,
                customer_id=201,
                product_id=102,
                quantity=1,
                total_amount=399.0,
                status="completed",
                payment_status="paid",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            # -------------------------------------------------
            # PRIYA
            # -------------------------------------------------

            Order(
                id=302,
                customer_id=202,
                product_id=101,
                quantity=1,
                total_amount=2499.0,
                status="completed",
                payment_status="paid",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            Order(
                id=303,
                customer_id=202,
                product_id=102,
                quantity=1,
                total_amount=399.0,
                status="completed",
                payment_status="paid",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            # -------------------------------------------------
            # ROHAN
            # -------------------------------------------------

            Order(
                id=304,
                customer_id=203,
                product_id=102,
                quantity=1,
                total_amount=399.0,
                status="completed",
                payment_status="paid",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            Order(
                id=305,
                customer_id=203,
                product_id=103,
                quantity=1,
                total_amount=699.0,
                status="completed",
                payment_status="paid",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            # -------------------------------------------------
            # ANANYA
            # -------------------------------------------------

            Order(
                id=306,
                customer_id=204,
                product_id=104,
                quantity=1,
                total_amount=899.0,
                status="completed",
                payment_status="paid",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            Order(
                id=307,
                customer_id=204,
                product_id=102,
                quantity=1,
                total_amount=399.0,
                status="completed",
                payment_status="paid",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            # -------------------------------------------------
            # KABIR
            # -------------------------------------------------

            Order(
                id=308,
                customer_id=205,
                product_id=101,
                quantity=1,
                total_amount=2499.0,
                status="completed",
                payment_status="paid",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            Order(
                id=309,
                customer_id=205,
                product_id=102,
                quantity=1,
                total_amount=399.0,
                status="completed",
                payment_status="paid",
                platform="direct",
                created_at=datetime.utcnow(),
            ),
        ]

        db.add_all(orders)

        db.flush()

        # =====================================================
        # TRANSACTIONS
        # =====================================================

        transactions = [

            Transaction(
                id=401,
                order_id=301,
                amount=399.0,
                payment_method="razorpay",
                status="success",
                payment_id="pay_demo_301",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            Transaction(
                id=402,
                order_id=302,
                amount=2499.0,
                payment_method="razorpay",
                status="success",
                payment_id="pay_demo_302",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            Transaction(
                id=403,
                order_id=303,
                amount=399.0,
                payment_method="razorpay",
                status="success",
                payment_id="pay_demo_303",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            Transaction(
                id=404,
                order_id=304,
                amount=399.0,
                payment_method="razorpay",
                status="success",
                payment_id="pay_demo_304",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            Transaction(
                id=405,
                order_id=305,
                amount=699.0,
                payment_method="razorpay",
                status="success",
                payment_id="pay_demo_305",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            Transaction(
                id=406,
                order_id=306,
                amount=899.0,
                payment_method="razorpay",
                status="success",
                payment_id="pay_demo_306",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            Transaction(
                id=407,
                order_id=307,
                amount=399.0,
                payment_method="razorpay",
                status="success",
                payment_id="pay_demo_307",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            Transaction(
                id=408,
                order_id=308,
                amount=2499.0,
                payment_method="razorpay",
                status="success",
                payment_id="pay_demo_308",
                platform="direct",
                created_at=datetime.utcnow(),
            ),

            Transaction(
                id=409,
                order_id=309,
                amount=399.0,
                payment_method="razorpay",
                status="success",
                payment_id="pay_demo_309",
                platform="direct",
                created_at=datetime.utcnow(),
            ),
        ]

        db.add_all(transactions)

        # =====================================================
        # PRIMARY BUILDATHON OPPORTUNITY
        # =====================================================

        opportunity = Opportunity(
            id=3,

            opportunity_type="cross_sell",

            title=(
                "Aarav may be ready for Running Shoes"
            ),

            description=(
                "Aarav recently purchased Sports Socks "
                "but has not purchased Running Shoes. "
                "Customers with this purchase pattern "
                "show a strong cross-sell opportunity."
            ),

            product_id=102,

            related_product_id=101,

            customer_count=1,

            estimated_value=2499.0,

            confidence="High",

            status="new",

            created_at=datetime.utcnow(),
        )

        db.add(opportunity)

        db.commit()

        print()
        print("=" * 60)
        print("MUNEEM DEMO DATA READY")
        print("=" * 60)

        print()
        print("Customer:")
        print("  Aarav")

        print()
        print("Previous purchase:")
        print("  Sports Socks — ₹399")

        print()
        print("Opportunity:")
        print("  Sports Socks → Running Shoes")

        print()
        print("Recommended product:")
        print("  Running Shoes — ₹2,499")

        print()
        print("Merchant policy:")
        print("  Maximum automatic discount: 5%")

        print()
        print("Expected personalized offer:")
        print("  ₹2,499 - ₹125 = ₹2,374")

        print()
        print("Opportunity ID:")
        print("  3")

        print()
        print("Next API call:")
        print("  POST /agent-actions/create/3")

        print()
        print("=" * 60)

    finally:
        db.close()


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    # Make sure all tables exist.
    Base.metadata.create_all(
        bind=engine
    )

    reset_database()
    seed_demo_data()