from datetime import datetime

import pandas as pd

from sqlalchemy.orm import Session

from src.backend.models.customer import Customer
from src.backend.models.product import Product
from src.backend.models.order import Order
from src.backend.models.transaction import Transaction


class DataImportService:

    # =========================================================
    # BASIC HELPERS
    # =========================================================

    def _clean(self, value):
        if value is None:
            return None

        try:
            if pd.isna(value):
                return None
        except Exception:
            pass

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return None

        return value

    def _float(self, value):
        value = self._clean(value)

        if value is None:
            return 0.0

        if isinstance(value, str):
            value = (
                value.replace("₹", "")
                .replace("$", "")
                .replace("€", "")
                .replace(",", "")
                .strip()
            )

        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _int(self, value):
        value = self._clean(value)

        if value is None:
            return 0

        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    def _date(self, value):
        value = self._clean(value)

        if value is None:
            return datetime.utcnow()

        if isinstance(value, datetime):
            return value

        try:
            return pd.to_datetime(value).to_pydatetime()
        except Exception:
            return datetime.utcnow()

    # =========================================================
    # MAPPING
    # =========================================================

    def _mapping(self, mappings):
        result = {}

        if not mappings:
            return result

        for item in mappings:
            source = item.get("source_column")
            target = item.get("target_field")

            if not source or not target:
                continue

            if target == "ignore":
                continue

            result.setdefault(target, []).append(source)

        return result

    def _value(self, row, mapping, field):
        sources = mapping.get(field, [])

        for source in sources:

            if source not in row:
                continue

            value = self._clean(row[source])

            if value is not None:
                return value

        return None

    # =========================================================
    # CUSTOMER
    # =========================================================

    def _find_customer(
        self,
        db: Session,
        value,
        row=None,
        mapping=None,
    ):
        value = self._clean(value)

        if value is None:
            return None

        value = str(value).strip()

        # -----------------------------------------------------
        # 1. Value itself is an email
        # -----------------------------------------------------

        if "@" in value:

            customer = (
                db.query(Customer)
                .filter(Customer.email == value)
                .first()
            )

            if customer:
                return customer

        # -----------------------------------------------------
        # 2. Exact name
        # -----------------------------------------------------

        customer = (
            db.query(Customer)
            .filter(Customer.name == value)
            .first()
        )

        if customer:
            return customer

        # -----------------------------------------------------
        # 3. Same row's email
        # -----------------------------------------------------

        if row is not None and mapping is not None:

            email = self._value(
                row,
                mapping,
                "customer_email",
            )

            if email:

                email = str(email).strip()

                customer = (
                    db.query(Customer)
                    .filter(Customer.email == email)
                    .first()
                )

                if customer:
                    return customer

        # -----------------------------------------------------
        # 4. Case-insensitive name
        # -----------------------------------------------------

        customers = db.query(Customer).all()

        value_lower = value.lower()

        for customer in customers:

            if (
                customer.name
                and customer.name.strip().lower()
                == value_lower
            ):
                return customer

        return None

    def _get_or_create_customer(
        self,
        db,
        row,
        mapping,
        customer_value=None,
    ):
        email = self._value(
            row,
            mapping,
            "customer_email",
        )

        name = self._value(
            row,
            mapping,
            "customer_name",
        )

        phone = self._value(
            row,
            mapping,
            "customer_phone",
        )

        # -----------------------------------------------------
        # Find by email
        # -----------------------------------------------------

        if email:

            email = str(email).strip()

            existing = (
                db.query(Customer)
                .filter(Customer.email == email)
                .first()
            )

            if existing:

                if name:
                    existing.name = str(name)

                if phone:
                    existing.phone = str(phone)

                return existing

        # -----------------------------------------------------
        # Find by name
        # -----------------------------------------------------

        lookup_value = name or customer_value

        if lookup_value:

            existing = self._find_customer(
                db,
                lookup_value,
                row,
                mapping,
            )

            if existing:

                if email and not existing.email:
                    existing.email = str(email)

                if phone:
                    existing.phone = str(phone)

                if name:
                    existing.name = str(name)

                return existing

        # -----------------------------------------------------
        # Customer identity requires email
        # -----------------------------------------------------

        if not email:
            return None

        customer = Customer(
            name=str(
                name
                or customer_value
                or "Unknown Customer"
            ),
            email=str(email),
            phone=str(phone or ""),
        )

        db.add(customer)
        db.flush()

        return customer

    # =========================================================
    # PRODUCT
    # =========================================================

    def _find_product(self, db, value):

        value = self._clean(value)

        if value is None:
            return None

        value = str(value).strip()

        # Exact match
        product = (
            db.query(Product)
            .filter(Product.name == value)
            .first()
        )

        if product:
            return product

        # Case-insensitive match
        products = db.query(Product).all()

        value_lower = value.lower()

        for product in products:

            if (
                product.name
                and product.name.strip().lower()
                == value_lower
            ):
                return product

        return None

    def _get_or_create_product(
        self,
        db,
        row,
        mapping,
        product_value,
    ):
        if not product_value:
            return None

        name = str(product_value).strip()

        existing = self._find_product(
            db,
            name,
        )

        # -----------------------------------------------------
        # Update existing product
        # -----------------------------------------------------

        if existing:

            price = self._float(
                self._value(
                    row,
                    mapping,
                    "product_price",
                )
            )

            if price > 0:
                existing.price = price

            description = self._value(
                row,
                mapping,
                "product_description",
            )

            if description:
                existing.description = str(
                    description
                )

            inventory = self._value(
                row,
                mapping,
                "product_inventory",
            )

            if inventory is not None:
                existing.inventory = self._int(
                    inventory
                )

            category = self._value(
                row,
                mapping,
                "product_category",
            )

            if category:
                existing.category = str(
                    category
                )

            return existing

        # -----------------------------------------------------
        # Create new product
        # -----------------------------------------------------

        product = Product(
            name=name,

            description=str(
                self._value(
                    row,
                    mapping,
                    "product_description",
                )
                or ""
            ),

            price=self._float(
                self._value(
                    row,
                    mapping,
                    "product_price",
                )
            ),

            inventory=self._int(
                self._value(
                    row,
                    mapping,
                    "product_inventory",
                )
            ),

            category=str(
                self._value(
                    row,
                    mapping,
                    "product_category",
                )
                or ""
            ),
        )

        db.add(product)
        db.flush()

        return product

    # =========================================================
    # ORDER DUPLICATE
    # =========================================================

    def _existing_order(
        self,
        db,
        customer_id,
        product_id,
        quantity,
        amount,
        created_at,
        platform,
    ):

        query = (
            db.query(Order)
            .filter(
                Order.customer_id == customer_id,
                Order.product_id == product_id,
                Order.quantity == quantity,
                Order.total_amount == amount,
            )
        )

        # Some versions of the Order model may not have
        # platform. Keep this compatible.
        if hasattr(Order, "platform"):
            query = query.filter(
                Order.platform == platform
            )

        orders = query.all()

        for order in orders:

            if not order.created_at:
                continue

            if order.created_at.date() == created_at.date():
                return order

        return None

    # =========================================================
    # TRANSACTION DUPLICATE
    # =========================================================

    def _existing_transaction(
        self,
        db,
        order_id,
        amount,
        payment_id,
        platform,
    ):

        # -----------------------------------------------------
        # Payment ID is the strongest duplicate key
        # -----------------------------------------------------

        if payment_id and hasattr(
            Transaction,
            "payment_id",
        ):

            query = (
                db.query(Transaction)
                .filter(
                    Transaction.payment_id
                    == str(payment_id),
                )
            )

            if hasattr(Transaction, "platform"):
                query = query.filter(
                    Transaction.platform
                    == platform
                )

            existing = query.first()

            if existing:
                return existing

        # -----------------------------------------------------
        # Fallback: order + amount
        # -----------------------------------------------------

        query = (
            db.query(Transaction)
            .filter(
                Transaction.order_id == order_id,
                Transaction.amount == amount,
            )
        )

        if hasattr(Transaction, "platform"):
            query = query.filter(
                Transaction.platform == platform
            )

        return query.first()

    # =========================================================
    # MAIN ENTRY
    # =========================================================

    def import_data(
        self,
        db: Session,
        dataframe: pd.DataFrame,
        mappings: list[dict],
        dataset_type: str,
        platform: str = "direct",
    ):

        # -----------------------------------------------------
        # Validate dataframe
        # -----------------------------------------------------

        if dataframe is None or dataframe.empty:

            return {
                "success": False,
                "message": "No data available for import.",
                "imported": 0,
                "skipped": 0,
            }

        platform = str(
            platform or "direct"
        ).strip().lower()

        dataset_type = str(
            dataset_type or ""
        ).strip().lower()

        mapping = self._mapping(mappings)

        imported = 0
        skipped = 0
        updated = 0
        duplicates = 0

        customers_imported = 0
        products_imported = 0
        orders_imported = 0
        transactions_imported = 0

        try:

            # =================================================
            # CUSTOMERS
            # =================================================

            if dataset_type == "customers":

                for _, row in dataframe.iterrows():

                    email = self._value(
                        row,
                        mapping,
                        "customer_email",
                    )

                    name = self._value(
                        row,
                        mapping,
                        "customer_name",
                    )

                    if not email:
                        skipped += 1
                        continue

                    existing = (
                        db.query(Customer)
                        .filter(
                            Customer.email
                            == str(email).strip()
                        )
                        .first()
                    )

                    customer = (
                        self._get_or_create_customer(
                            db,
                            row,
                            mapping,
                        )
                    )

                    if customer:

                        if existing:
                            updated += 1
                        else:
                            imported += 1
                            customers_imported += 1

                db.commit()

                return {
                    "success": True,
                    "imported": imported,
                    "customers_imported": customers_imported,
                    "updated": updated,
                    "skipped": skipped,
                    "duplicates": duplicates,
                }

            # =================================================
            # PRODUCTS
            # =================================================

            if dataset_type == "products":

                for _, row in dataframe.iterrows():

                    product_name = self._value(
                        row,
                        mapping,
                        "product_name",
                    )

                    if not product_name:
                        skipped += 1
                        continue

                    existing = self._find_product(
                        db,
                        product_name,
                    )

                    product = (
                        self._get_or_create_product(
                            db,
                            row,
                            mapping,
                            product_name,
                        )
                    )

                    if product:

                        if existing:
                            updated += 1
                        else:
                            imported += 1
                            products_imported += 1

                db.commit()

                return {
                    "success": True,
                    "imported": imported,
                    "products_imported": products_imported,
                    "updated": updated,
                    "skipped": skipped,
                    "duplicates": duplicates,
                }

            # =================================================
            # ORDERS
            # =================================================

            if dataset_type == "orders":

                for _, row in dataframe.iterrows():

                    customer_value = self._value(
                        row,
                        mapping,
                        "order_customer",
                    )

                    product_value = self._value(
                        row,
                        mapping,
                        "order_product",
                    )

                    if (
                        not customer_value
                        or not product_value
                    ):
                        skipped += 1
                        continue

                    # -----------------------------------------
                    # Customer
                    # -----------------------------------------

                    customer = self._find_customer(
                        db,
                        customer_value,
                        row,
                        mapping,
                    )

                    if not customer:

                        customer = (
                            self._get_or_create_customer(
                                db,
                                row,
                                mapping,
                                customer_value,
                            )
                        )

                    # -----------------------------------------
                    # Product
                    # -----------------------------------------

                    product = self._find_product(
                        db,
                        product_value,
                    )

                    if not product:

                        product = (
                            self._get_or_create_product(
                                db,
                                row,
                                mapping,
                                product_value,
                            )
                        )

                    if not customer or not product:

                        skipped += 1
                        continue

                    # -----------------------------------------
                    # Quantity
                    # -----------------------------------------

                    quantity = self._int(
                        self._value(
                            row,
                            mapping,
                            "order_quantity",
                        )
                    )

                    if quantity <= 0:
                        quantity = 1

                    # -----------------------------------------
                    # Amount
                    # -----------------------------------------

                    amount = self._float(
                        self._value(
                            row,
                            mapping,
                            "order_total_amount",
                        )
                    )

                    # -----------------------------------------
                    # Date
                    # -----------------------------------------

                    created_at = self._date(
                        self._value(
                            row,
                            mapping,
                            "order_created_at",
                        )
                    )

                    # -----------------------------------------
                    # Duplicate check
                    # -----------------------------------------

                    existing = self._existing_order(
                        db,
                        customer.id,
                        product.id,
                        quantity,
                        amount,
                        created_at,
                        platform,
                    )

                    if existing:

                        duplicates += 1
                        continue

                    # -----------------------------------------
                    # Create order
                    # -----------------------------------------

                    order_data = {
                        "customer_id": customer.id,
                        "product_id": product.id,
                        "quantity": quantity,
                        "total_amount": amount,
                        "created_at": created_at,
                    }

                    if hasattr(Order, "platform"):
                        order_data["platform"] = platform

                    order = Order(
                        **order_data
                    )

                    # -----------------------------------------
                    # Status
                    # -----------------------------------------

                    status = self._value(
                        row,
                        mapping,
                        "order_status",
                    )

                    if status and hasattr(
                        order,
                        "status",
                    ):
                        order.status = str(status)

                    # -----------------------------------------
                    # Payment status
                    # -----------------------------------------

                    payment_status = self._value(
                        row,
                        mapping,
                        "order_payment_status",
                    )

                    if (
                        payment_status
                        and hasattr(
                            order,
                            "payment_status",
                        )
                    ):
                        order.payment_status = str(
                            payment_status
                        )

                    db.add(order)

                    # -----------------------------------------
                    # Update customer aggregates
                    # -----------------------------------------

                    if hasattr(
                        customer,
                        "total_orders",
                    ):
                        customer.total_orders = (
                            customer.total_orders or 0
                        ) + 1

                    if hasattr(
                        customer,
                        "total_spent",
                    ):
                        customer.total_spent = (
                            customer.total_spent or 0
                        ) + amount

                    imported += 1
                    orders_imported += 1

                db.commit()

                return {
                    "success": True,
                    "imported": imported,
                    "orders_imported": orders_imported,
                    "duplicates": duplicates,
                    "skipped": skipped,
                }

            # =================================================
            # TRANSACTIONS
            # =================================================

            if dataset_type == "transactions":

                for _, row in dataframe.iterrows():

                    transaction_order = self._value(
                        row,
                        mapping,
                        "transaction_order",
                    )

                    order = None

                    # -----------------------------------------
                    # Resolve order ID
                    # -----------------------------------------

                    if transaction_order:

                        try:

                            order_id = int(
                                float(
                                    transaction_order
                                )
                            )

                            order_query = (
                                db.query(Order)
                                .filter(
                                    Order.id == order_id
                                )
                            )

                            if hasattr(
                                Order,
                                "platform",
                            ):
                                order_query = (
                                    order_query.filter(
                                        Order.platform
                                        == platform
                                    )
                                )

                            order = (
                                order_query.first()
                            )

                        except (
                            ValueError,
                            TypeError,
                        ):
                            order = None

                    if not order:

                        skipped += 1
                        continue

                    # -----------------------------------------
                    # Transaction fields
                    # -----------------------------------------

                    amount = self._float(
                        self._value(
                            row,
                            mapping,
                            "transaction_amount",
                        )
                    )

                    payment_id = self._value(
                        row,
                        mapping,
                        "transaction_payment_id",
                    )

                    payment_method = self._value(
                        row,
                        mapping,
                        "transaction_payment_method",
                    )

                    status = self._value(
                        row,
                        mapping,
                        "transaction_status",
                    )

                    created_at = self._date(
                        self._value(
                            row,
                            mapping,
                            "transaction_created_at",
                        )
                    )

                    # -----------------------------------------
                    # Duplicate check
                    # -----------------------------------------

                    existing = (
                        self._existing_transaction(
                            db,
                            order.id,
                            amount,
                            payment_id,
                            platform,
                        )
                    )

                    if existing:

                        duplicates += 1
                        continue

                    # -----------------------------------------
                    # Build transaction dynamically
                    # -----------------------------------------
                    # This keeps the importer compatible with
                    # slightly different Transaction models.

                    transaction_data = {
                        "order_id": order.id,
                        "amount": amount,
                    }

                    if hasattr(
                        Transaction,
                        "payment_id",
                    ):
                        transaction_data[
                            "payment_id"
                        ] = (
                            str(payment_id)
                            if payment_id
                            else None
                        )

                    if hasattr(
                        Transaction,
                        "platform",
                    ):
                        transaction_data[
                            "platform"
                        ] = platform

                    if hasattr(
                        Transaction,
                        "payment_method",
                    ):
                        transaction_data[
                            "payment_method"
                        ] = (
                            str(payment_method)
                            if payment_method
                            else None
                        )

                    if hasattr(
                        Transaction,
                        "status",
                    ):
                        transaction_data[
                            "status"
                        ] = (
                            str(status)
                            if status
                            else None
                        )

                    if hasattr(
                        Transaction,
                        "created_at",
                    ):
                        transaction_data[
                            "created_at"
                        ] = created_at

                    transaction = Transaction(
                        **transaction_data
                    )

                    db.add(transaction)

                    imported += 1
                    transactions_imported += 1

                db.commit()

                return {
                    "success": True,
                    "imported": imported,
                    "transactions_imported": (
                        transactions_imported
                    ),
                    "duplicates": duplicates,
                    "skipped": skipped,
                }

            # =================================================
            # UNKNOWN DATASET TYPE
            # =================================================

            return {
                "success": False,
                "message": (
                    f"Unsupported dataset type: "
                    f"{dataset_type}"
                ),
                "imported": 0,
                "skipped": len(dataframe),
            }

        except Exception:
            db.rollback()
            raise


# =========================================================
# SERVICE INSTANCE
# =========================================================
#
# IMPORTANT:
# data_routes.py imports this exact variable:
#
# from src.backend.services.data_import_service import (
#     data_import_service,
# )
#
# Therefore this instance MUST exist.
# =========================================================

data_import_service = DataImportService()