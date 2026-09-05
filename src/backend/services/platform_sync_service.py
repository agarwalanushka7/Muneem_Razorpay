from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from src.backend.models.platform import Platform
from src.backend.models.product import Product
from src.backend.models.customer import Customer
from src.backend.models.order import Order
from src.backend.models.transaction import Transaction


class PlatformSyncService:

    # =========================================================
    # GET PLATFORM
    # =========================================================

    def get_platform(
        self,
        db: Session,
        platform_id: int,
    ) -> Platform | None:

        return (
            db.query(Platform)
            .filter(
                Platform.id == platform_id
            )
            .first()
        )

    # =========================================================
    # NORMALIZE PLATFORM NAME
    # =========================================================

    def normalize_platform_name(
        self,
        platform: Platform,
    ) -> str:

        return platform.name.strip().lower()

    # =========================================================
    # SYNC PLATFORM DATA
    # =========================================================

    def sync_platform_data(
        self,
        db: Session,
        platform_id: int,
        data: dict[str, Any],
    ) -> dict:

        platform = self.get_platform(
            db=db,
            platform_id=platform_id,
        )

        if platform is None:
            return {
                "success": False,
                "message": "Platform not found.",
            }

        platform_name = (
            self.normalize_platform_name(
                platform
            )
        )

        products_data = data.get(
            "products",
            [],
        )

        customers_data = data.get(
            "customers",
            [],
        )

        orders_data = data.get(
            "orders",
            [],
        )

        transactions_data = data.get(
            "transactions",
            [],
        )

        created_products = 0
        updated_products = 0

        created_customers = 0
        updated_customers = 0

        created_orders = 0
        updated_orders = 0

        created_transactions = 0
        updated_transactions = 0

        try:

            # =================================================
            # PRODUCTS
            # =================================================

            for item in products_data:

                product_id = item.get("id")

                if product_id is None:
                    continue

                product = (
                    db.query(Product)
                    .filter(
                        Product.id
                        == product_id
                    )
                    .first()
                )

                if product:

                    product.name = item.get(
                        "name",
                        product.name,
                    )

                    product.price = float(
                        item.get(
                            "price",
                            product.price,
                        )
                    )

                    product.inventory = int(
                        item.get(
                            "inventory",
                            product.inventory,
                        )
                    )

                    updated_products += 1

                else:

                    product = Product(
                        id=product_id,
                        name=item.get(
                            "name",
                            "Unknown Product",
                        ),
                        price=float(
                            item.get(
                                "price",
                                0,
                            )
                        ),
                        inventory=int(
                            item.get(
                                "inventory",
                                0,
                            )
                        ),
                    )

                    db.add(product)
                    created_products += 1

            db.flush()

            # =================================================
            # CUSTOMERS
            # =================================================

            for item in customers_data:

                customer_id = item.get("id")
                email = item.get("email")

                customer = None

                # First try ID
                if customer_id is not None:

                    customer = (
                        db.query(Customer)
                        .filter(
                            Customer.id
                            == customer_id
                        )
                        .first()
                    )

                # If no ID match, try email
                if (
                    customer is None
                    and email
                ):

                    customer = (
                        db.query(Customer)
                        .filter(
                            Customer.email
                            == email
                        )
                        .first()
                    )

                if customer:

                    customer.name = item.get(
                        "name",
                        customer.name,
                    )

                    if email:
                        customer.email = email

                    updated_customers += 1

                else:

                    customer = Customer(
                        id=customer_id,
                        name=item.get(
                            "name",
                            "Unknown Customer",
                        ),
                        email=email,
                    )

                    db.add(customer)
                    created_customers += 1

            db.flush()

            # =================================================
            # ORDERS
            # =================================================

            for item in orders_data:

                order_id = item.get("id")

                if order_id is None:
                    continue

                existing_order = (
                    db.query(Order)
                    .filter(
                        Order.id
                        == order_id
                    )
                    .first()
                )

                customer_id = item.get(
                    "customer_id"
                )

                product_id = item.get(
                    "product_id"
                )

                customer_exists = (
                    db.query(Customer)
                    .filter(
                        Customer.id
                        == customer_id
                    )
                    .first()
                )

                product_exists = (
                    db.query(Product)
                    .filter(
                        Product.id
                        == product_id
                    )
                    .first()
                )

                if (
                    customer_exists is None
                    or product_exists is None
                ):
                    continue

                if existing_order:

                    existing_order.customer_id = (
                        customer_id
                    )

                    existing_order.product_id = (
                        product_id
                    )

                    existing_order.quantity = int(
                        item.get(
                            "quantity",
                            existing_order.quantity,
                        )
                    )

                    existing_order.total_amount = (
                        float(
                            item.get(
                                "total_amount",
                                existing_order.total_amount,
                            )
                        )
                    )

                    existing_order.status = (
                        item.get(
                            "status",
                            existing_order.status,
                        )
                    )

                    existing_order.payment_status = (
                        item.get(
                            "payment_status",
                            existing_order.payment_status,
                        )
                    )

                    existing_order.platform = (
                        platform_name
                    )

                    updated_orders += 1

                else:

                    order = Order(
                        id=order_id,
                        customer_id=customer_id,
                        product_id=product_id,
                        quantity=int(
                            item.get(
                                "quantity",
                                1,
                            )
                        ),
                        total_amount=float(
                            item.get(
                                "total_amount",
                                0,
                            )
                        ),
                        status=item.get(
                            "status",
                            "completed",
                        ),
                        payment_status=item.get(
                            "payment_status",
                            "paid",
                        ),
                        platform=platform_name,
                    )

                    db.add(order)
                    created_orders += 1

            db.flush()

            # =================================================
            # TRANSACTIONS
            # =================================================

            for item in transactions_data:

                transaction_id = item.get(
                    "id"
                )

                if transaction_id is None:
                    continue

                existing_transaction = (
                    db.query(Transaction)
                    .filter(
                        Transaction.id
                        == transaction_id
                    )
                    .first()
                )

                order_id = item.get(
                    "order_id"
                )

                order_exists = (
                    db.query(Order)
                    .filter(
                        Order.id
                        == order_id
                    )
                    .first()
                )

                if order_exists is None:
                    continue

                if existing_transaction:

                    existing_transaction.order_id = (
                        order_id
                    )

                    existing_transaction.amount = (
                        float(
                            item.get(
                                "amount",
                                existing_transaction.amount,
                            )
                        )
                    )

                    existing_transaction.payment_method = (
                        item.get(
                            "payment_method",
                            existing_transaction.payment_method,
                        )
                    )

                    existing_transaction.status = (
                        item.get(
                            "status",
                            existing_transaction.status,
                        )
                    )

                    existing_transaction.payment_id = (
                        item.get(
                            "payment_id",
                            existing_transaction.payment_id,
                        )
                    )

                    existing_transaction.platform = (
                        platform_name
                    )

                    updated_transactions += 1

                else:

                    transaction = Transaction(
                        id=transaction_id,
                        order_id=order_id,
                        amount=float(
                            item.get(
                                "amount",
                                0,
                            )
                        ),
                        payment_method=item.get(
                            "payment_method",
                            "razorpay",
                        ),
                        status=item.get(
                            "status",
                            "success",
                        ),
                        payment_id=item.get(
                            "payment_id"
                        ),
                        platform=platform_name,
                    )

                    db.add(transaction)
                    created_transactions += 1

            # =================================================
            # UPDATE PLATFORM
            # =================================================

            platform.status = "connected"
            platform.is_active = True
            platform.last_synced_at = (
                datetime.utcnow()
            )

            db.commit()

            return {
                "success": True,
                "platform_id": platform.id,
                "platform": platform.display_name,
                "status": platform.status,

                "created": {
                    "products": created_products,
                    "customers": created_customers,
                    "orders": created_orders,
                    "transactions": created_transactions,
                },

                "updated": {
                    "products": updated_products,
                    "customers": updated_customers,
                    "orders": updated_orders,
                    "transactions": updated_transactions,
                },

                "message": (
                    f"{platform.display_name} "
                    "data synchronized successfully."
                ),
            }

        except Exception as exc:

            db.rollback()

            return {
                "success": False,
                "platform": platform.display_name,
                "message": (
                    "Platform synchronization failed."
                ),
                "error": str(exc),
            }


platform_sync_service = PlatformSyncService()