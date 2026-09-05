from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from src.backend.core.config import settings


# =========================================================
# FIELD MAPPING
# =========================================================


class FieldMapping(BaseModel):
    source_column: str = Field(
        description=(
            "Exact column or field name identified "
            "in the merchant data."
        )
    )

    target_field: Literal[
        # Customer
        "customer_name",
        "customer_email",
        "customer_phone",

        # Product
        "product_name",
        "product_description",
        "product_price",
        "product_inventory",
        "product_category",

        # Order
        "order_customer",
        "order_product",
        "order_quantity",
        "order_total_amount",
        "order_status",
        "order_payment_status",
        "order_created_at",

        # Transaction
        "transaction_order",
        "transaction_amount",
        "transaction_payment_method",
        "transaction_status",
        "transaction_payment_id",
        "transaction_created_at",

        # Ignore
        "ignore",
    ]

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence in the mapping, "
            "between 0 and 1."
        ),
    )


# =========================================================
# COMPLETE DATA MAPPING
# =========================================================


class DataMapping(BaseModel):

    dataset_type: Literal[
        "customers",
        "products",
        "orders",
        "transactions",
        "mixed",
        "unknown",
    ]

    mappings: list[FieldMapping]

    explanation: str = Field(
        description=(
            "Brief explanation of how the "
            "merchant's business data was understood."
        )
    )


# =========================================================
# DATA MAPPING SERVICE
# =========================================================


class DataMappingService:

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    # =====================================================
    # GEMINI CALL
    # =====================================================

    def _generate_mapping(
        self,
        prompt: str,
    ) -> DataMapping:

        response = (
            self.client.models.generate_content(
                model=settings.gemini_model.strip(),
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=DataMapping,
                ),
            )
        )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        return DataMapping.model_validate_json(
            response.text
        )

    # =====================================================
    # LOCAL FALLBACK HELPERS
    # =====================================================

    def _normalize_column(self, column: str) -> str:
        """
        Normalize a column name so the local fallback
        can recognize common variations.
        """

        return (
            str(column)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
            .replace(".", " ")
            .replace("/", " ")
        )

    def _contains_any(
        self,
        value: str,
        words: set[str],
    ) -> bool:

        return any(
            word in value
            for word in words
        )

    # =====================================================
    # LOCAL STRUCTURED FILE FALLBACK
    # =====================================================

    def _generate_local_mapping(
        self,
        columns: list[str],
        sample_rows: list[dict],
    ) -> DataMapping:

        """
        Deterministic fallback used when Gemini is
        temporarily unavailable.

        This mapper NEVER invents source columns.
        It only maps columns whose names clearly
        indicate their meaning.

        Ambiguous columns are mapped to "ignore".
        """

        mappings: list[FieldMapping] = []

        normalized_columns = {
            column: self._normalize_column(column)
            for column in columns
        }

        # -------------------------------------------------
        # Detect whether the file appears transaction-heavy
        # -------------------------------------------------

        normalized_values = list(
            normalized_columns.values()
        )

        has_transaction_signal = any(
            self._contains_any(
                value,
                {
                    "payment method",
                    "payment id",
                    "transaction id",
                    "transaction status",
                    "transaction date",
                    "transaction amount",
                },
            )
            for value in normalized_values
        )

        has_order_signal = any(
            self._contains_any(
                value,
                {
                    "order id",
                    "order date",
                    "purchase date",
                    "sale date",
                    "quantity",
                    "order status",
                    "order amount",
                    "total amount",
                },
            )
            for value in normalized_values
        )

        used_targets: set[str] = set()

        def add_mapping(
            source: str,
            target: str,
            confidence: float,
        ):

            # Never create duplicate target mappings
            # except where the same source is intentionally
            # mapped to both a business entity and a
            # relationship field.
            if target in used_targets:
                return

            mappings.append(
                FieldMapping(
                    source_column=source,
                    target_field=target,
                    confidence=confidence,
                )
            )

            used_targets.add(target)

        # -------------------------------------------------
        # COLUMN-LEVEL HEURISTICS
        # -------------------------------------------------

        for column, normalized in normalized_columns.items():

            # =============================================
            # EMAIL
            # =============================================

            if (
                "email" in normalized
                or "e mail" in normalized
            ):

                add_mapping(
                    column,
                    "customer_email",
                    0.99,
                )

                continue

            # =============================================
            # PHONE
            # =============================================

            if self._contains_any(
                normalized,
                {
                    "phone",
                    "mobile",
                    "contact number",
                    "phone number",
                },
            ):

                add_mapping(
                    column,
                    "customer_phone",
                    0.96,
                )

                continue

            # =============================================
            # CUSTOMER NAME
            # =============================================

            if (
                "customer name" in normalized
                or "customer" == normalized
                or "buyer name" in normalized
                or "buyer" == normalized
                or "client name" in normalized
            ):

                add_mapping(
                    column,
                    "customer_name",
                    0.96,
                )

                continue

            # =============================================
            # PRODUCT DESCRIPTION
            # =============================================

            if (
                "product description" in normalized
                or "description" == normalized
                or "item description" in normalized
            ):

                add_mapping(
                    column,
                    "product_description",
                    0.94,
                )

                continue

            # =============================================
            # PRODUCT INVENTORY
            # =============================================

            if self._contains_any(
                normalized,
                {
                    "inventory",
                    "stock",
                    "stock quantity",
                    "available stock",
                },
            ):

                add_mapping(
                    column,
                    "product_inventory",
                    0.94,
                )

                continue

            # =============================================
            # PRODUCT CATEGORY
            # =============================================

            if (
                "product category" in normalized
                or normalized == "category"
                or "item category" in normalized
            ):

                add_mapping(
                    column,
                    "product_category",
                    0.94,
                )

                continue

            # =============================================
            # PAYMENT METHOD
            # =============================================

            if self._contains_any(
                normalized,
                {
                    "payment method",
                    "payment mode",
                    "payment type",
                },
            ):

                add_mapping(
                    column,
                    "transaction_payment_method",
                    0.98,
                )

                continue

            # =============================================
            # PAYMENT ID
            # =============================================

            if (
                "payment id" in normalized
                or "transaction id" in normalized
                or "txn id" in normalized
            ):

                add_mapping(
                    column,
                    "transaction_payment_id",
                    0.95,
                )

                continue

            # =============================================
            # TRANSACTION STATUS
            # =============================================

            if (
                "transaction status" in normalized
            ):

                add_mapping(
                    column,
                    "transaction_status",
                    0.96,
                )

                continue

            # =============================================
            # ORDER PAYMENT STATUS
            # =============================================

            if (
                "order payment status"
                in normalized
            ):

                add_mapping(
                    column,
                    "order_payment_status",
                    0.96,
                )

                continue

            # =============================================
            # ORDER STATUS
            # =============================================

            if (
                "order status" in normalized
                or normalized == "status"
            ):

                if has_transaction_signal:
                    add_mapping(
                        column,
                        "order_status",
                        0.75,
                    )
                else:
                    add_mapping(
                        column,
                        "order_status",
                        0.90,
                    )

                continue

            # =============================================
            # QUANTITY
            # =============================================

            if self._contains_any(
                normalized,
                {
                    "quantity",
                    "qty",
                    "units",
                    "units sold",
                },
            ):

                add_mapping(
                    column,
                    "order_quantity",
                    0.98,
                )

                continue

            # =============================================
            # ORDER DATE
            # =============================================

            if self._contains_any(
                normalized,
                {
                    "purchase date",
                    "order date",
                    "sale date",
                    "purchase time",
                    "order time",
                },
            ):

                add_mapping(
                    column,
                    "order_created_at",
                    0.96,
                )

                continue

            # =============================================
            # TRANSACTION DATE
            # =============================================

            if (
                "transaction date" in normalized
                or "transaction time" in normalized
            ):

                add_mapping(
                    column,
                    "transaction_created_at",
                    0.96,
                )

                continue

            # =============================================
            # ORDER ID
            # =============================================

            if (
                normalized == "order id"
                or "order identifier" in normalized
            ):

                if has_transaction_signal:
                    add_mapping(
                        column,
                        "transaction_order",
                        0.95,
                    )

                continue

            # =============================================
            # PRODUCT PRICE
            # =============================================

            if self._contains_any(
                normalized,
                {
                    "product price",
                    "unit price",
                    "selling price",
                    "item price",
                    "mrp",
                },
            ):

                add_mapping(
                    column,
                    "product_price",
                    0.94,
                )

                continue

            # =============================================
            # PRODUCT NAME
            # =============================================

            if (
                normalized == "product"
                or normalized == "product name"
                or "item name" in normalized
                or normalized == "item"
                or "sku name" in normalized
            ):

                add_mapping(
                    column,
                    "product_name",
                    0.95,
                )

                continue

            # =============================================
            # TOTAL / AMOUNT
            # =============================================

            if self._contains_any(
                normalized,
                {
                    "order total",
                    "order amount",
                    "total amount",
                    "total value",
                    "sale amount",
                    "sales amount",
                },
            ):

                add_mapping(
                    column,
                    "order_total_amount",
                    0.90,
                )

                continue

            if (
                normalized == "amount"
                or normalized == "value"
                or normalized == "revenue"
            ):

                if has_transaction_signal and not has_order_signal:
                    add_mapping(
                        column,
                        "transaction_amount",
                        0.80,
                    )
                else:
                    add_mapping(
                        column,
                        "order_total_amount",
                        0.78,
                    )

                continue

            # =============================================
            # GENERIC NAME
            # =============================================

            if normalized == "name":

                add_mapping(
                    column,
                    "customer_name",
                    0.60,
                )

                continue

        # -------------------------------------------------
        # HANDLE COMMON MIXED-DATA RELATIONSHIPS
        # -------------------------------------------------

        """
        The local fallback cannot safely duplicate every
        relationship the way Gemini can.

        However, for extremely common mixed datasets,
        we can add a second mapping for obvious Customer
        and Product columns.
        """

        existing_pairs = {
            (
                item.source_column,
                item.target_field,
            )
            for item in mappings
        }

        for column, normalized in normalized_columns.items():

            # Customer Name can represent both the customer
            # entity and the customer referenced by an order.
            if (
                "customer name" in normalized
                or "buyer name" in normalized
                or "client name" in normalized
            ):

                pair = (
                    column,
                    "order_customer",
                )

                if pair not in existing_pairs:

                    mappings.append(
                        FieldMapping(
                            source_column=column,
                            target_field="order_customer",
                            confidence=0.93,
                        )
                    )

                    existing_pairs.add(pair)

            # Product / Item can represent both the product
            # entity and the product purchased in an order.
            if (
                normalized == "product"
                or normalized == "product name"
                or normalized == "item"
                or "item name" in normalized
            ):

                pair = (
                    column,
                    "order_product",
                )

                if pair not in existing_pairs:

                    mappings.append(
                        FieldMapping(
                            source_column=column,
                            target_field="order_product",
                            confidence=0.92,
                        )
                    )

                    existing_pairs.add(pair)

        # -------------------------------------------------
        # DATASET TYPE
        # -------------------------------------------------

        targets = {
            mapping.target_field
            for mapping in mappings
        }

        has_customer = any(
            target.startswith("customer_")
            or target == "order_customer"
            for target in targets
        )

        has_product = any(
            target.startswith("product_")
            or target == "order_product"
            for target in targets
        )

        has_order = any(
            target.startswith("order_")
            for target in targets
        )

        has_transaction = any(
            target.startswith("transaction_")
            for target in targets
        )

        entity_count = sum(
            [
                has_customer,
                has_product,
                has_order,
                has_transaction,
            ]
        )

        if entity_count >= 2:
            dataset_type = "mixed"
        elif has_transaction:
            dataset_type = "transactions"
        elif has_order:
            dataset_type = "orders"
        elif has_product:
            dataset_type = "products"
        elif has_customer:
            dataset_type = "customers"
        else:
            dataset_type = "unknown"

        # -------------------------------------------------
        # IF NOTHING WAS RECOGNIZED
        # -------------------------------------------------

        if not mappings:

            mappings = [
                FieldMapping(
                    source_column=column,
                    target_field="ignore",
                    confidence=0.20,
                )
                for column in columns
            ]

            dataset_type = "unknown"

        return DataMapping(
            dataset_type=dataset_type,
            mappings=mappings,
            explanation=(
                "Gemini was temporarily unavailable, "
                "so MUNEEM used deterministic local "
                "column matching. The mapping should "
                "be reviewed before import."
            ),
        )

    # =====================================================
    # STRUCTURED FILE MAPPING
    # =====================================================

    def generate_mapping(
        self,
        columns: list[str],
        sample_rows: list[dict],
    ) -> DataMapping:

        prompt = f"""
You are the data onboarding intelligence
for an AI revenue management platform.

A merchant has uploaded a business data file.

Your job is to understand the structure of
the merchant's data and map the available
columns to our internal business fields.

You MUST work only with the evidence provided.

==================================================
MERCHANT COLUMNS
==================================================

{columns}


==================================================
SAMPLE DATA
==================================================

{sample_rows}


==================================================
SUPPORTED INTERNAL FIELDS
==================================================

CUSTOMER:

- customer_name
- customer_email
- customer_phone


PRODUCT:

- product_name
- product_description
- product_price
- product_inventory
- product_category


ORDER:

- order_customer
- order_product
- order_quantity
- order_total_amount
- order_status
- order_payment_status
- order_created_at


TRANSACTION:

- transaction_order
- transaction_amount
- transaction_payment_method
- transaction_status
- transaction_payment_id
- transaction_created_at


OTHER:

- ignore


==================================================
IMPORTANT MAPPING RULES
==================================================

1. Use only evidence contained in the
   merchant columns and sample rows.

2. NEVER invent a column.

3. NEVER invent a customer, product,
   order, transaction, price, date,
   quantity or payment.

4. Preserve the source column name exactly
   as provided.

5. Map a source column to the most appropriate
   internal field.

6. A source column MAY map to more than one
   internal field when the same information
   legitimately represents different business
   relationships.

7. DO NOT create duplicate mappings to the
   same target field.

8. If a column is ambiguous, prefer "ignore"
   instead of guessing.

9. Do not confuse:

   product_price

   with:

   order_total_amount

10. Do not confuse:

   order_total_amount

   with:

   transaction_amount

11. Quantity should normally map to:

   order_quantity

12. Payment method should normally map to:

   transaction_payment_method

13. Purchase date, order date or sale date
    should normally map to:

   order_created_at

14. Transaction date should map to:

   transaction_created_at

    only when the data clearly represents
    a payment transaction.

15. Determine the overall dataset type.

16. Use "mixed" when the same dataset contains
    information belonging to multiple business
    entities.

17. Give every mapping a confidence score
    between 0 and 1.

18. Do not make any decision about:

    discounts
    pricing
    payments
    automatic execution
    merchant approval

19. Your task is ONLY to understand and map
    the merchant data.

==================================================
OUTPUT
==================================================

Return ONLY the structured mapping.

Do not include additional commentary outside
the requested structure.
"""

        try:

            return self._generate_mapping(
                prompt
            )

        except Exception as e:

            error_text = str(e).lower()

            temporary_failure = any(
                indicator in error_text
                for indicator in [
                    "503",
                    "429",
                    "unavailable",
                    "high demand",
                    "resource exhausted",
                    "rate limit",
                    "temporarily",
                    "overloaded",
                    "deadline exceeded",
                ]
            )

            if temporary_failure:

                print(
                    "Gemini mapping unavailable. "
                    "Using local fallback mapping: "
                    f"{e}"
                )

                return self._generate_local_mapping(
                    columns=columns,
                    sample_rows=sample_rows,
                )

            # For non-temporary errors we still use
            # the fallback so merchant imports are not
            # unnecessarily blocked by an AI formatting
            # or response issue.

            print(
                "Gemini mapping failed. "
                "Using local fallback mapping: "
                f"{e}"
            )

            return self._generate_local_mapping(
                columns=columns,
                sample_rows=sample_rows,
            )

    # =====================================================
    # PDF MAPPING
    # =====================================================

    def generate_mapping_from_pdf(
        self,
        text: str,
    ) -> DataMapping:

        prompt = f"""
You are the data onboarding intelligence
for an AI revenue management platform.

A merchant has uploaded a PDF containing
business information.

Your task is to understand the information
contained in the PDF and identify useful
business fields.

==================================================
PDF CONTENT
==================================================

{text}


==================================================
SUPPORTED INTERNAL FIELDS
==================================================

CUSTOMER:

- customer_name
- customer_email
- customer_phone


PRODUCT:

- product_name
- product_description
- product_price
- product_inventory
- product_category


ORDER:

- order_customer
- order_product
- order_quantity
- order_total_amount
- order_status
- order_payment_status
- order_created_at


TRANSACTION:

- transaction_order
- transaction_amount
- transaction_payment_method
- transaction_status
- transaction_payment_id
- transaction_created_at


OTHER:

- ignore


==================================================
PDF ANALYSIS RULES
==================================================

1. Use ONLY information actually present
   in the PDF.

2. NEVER invent customers, products,
   orders, transactions, prices or dates.

3. Identify field names as they appear in
   the PDF whenever possible.

4. If the PDF contains a table, identify
   the table columns.

5. If the PDF contains multiple tables,
   identify useful fields across those tables.

6. A source field MAY map to multiple internal
   fields when the same information legitimately
   represents multiple business relationships.

7. Do not confuse product price with order
   total amount.

8. Do not confuse order amount with
   transaction amount.

9. Use "ignore" for information that does
   not correspond to our supported fields.

10. If the document is ambiguous, do not guess.

11. Determine whether the PDF represents:

    customers
    products
    orders
    transactions
    mixed
    unknown

12. Give every mapping a confidence score
    between 0 and 1.

13. Do not make decisions about discounts,
    payments, pricing or automatic execution.

14. Your task is ONLY to understand the
    business data contained in the PDF.

==================================================
OUTPUT
==================================================

Return ONLY the structured mapping.
"""

        try:

            return self._generate_mapping(
                prompt
            )

        except Exception as e:

            print(
                "Gemini PDF mapping failed: "
                f"{e}"
            )

            # PDF fallback intentionally remains
            # conservative. Unlike spreadsheets,
            # PDF text does not reliably expose exact
            # source columns.

            return DataMapping(
                dataset_type="unknown",
                mappings=[],
                explanation=(
                    "AI PDF analysis was temporarily "
                    "unavailable. No fields were guessed. "
                    "Please retry the analysis."
                ),
            )


# =========================================================
# SINGLE SERVICE INSTANCE
# =========================================================


data_mapping_service = DataMappingService()