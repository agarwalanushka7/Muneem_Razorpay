from typing import Any

import pandas as pd

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from pydantic import BaseModel

from sqlalchemy.orm import Session

from src.backend.database import get_db

from src.backend.models.platform import Platform
from src.backend.models.customer import Customer
from src.backend.models.product import Product
from src.backend.models.order import Order
from src.backend.models.opportunity import Opportunity

from src.backend.services.data_ingestion_service import (
    data_ingestion_service,
)

from src.backend.services.data_mapping_service import (
    data_mapping_service,
)

from src.backend.services.upload_session_service import (
    upload_session_service,
)

from src.backend.services.data_import_service import (
    data_import_service,
)

from src.backend.services.opportunity_service import (
    detect_cross_sell_opportunities,
)

from src.backend.services.revenue_agent_service import (
    run_revenue_agent,
)


router = APIRouter(
    prefix="/data",
    tags=["Merchant Data"],
)


# =========================================================
# REQUEST SCHEMAS
# =========================================================


class MappingApproval(BaseModel):
    source_column: str
    target_field: str


class ImportConfirmation(BaseModel):
    dataset_type: str
    mappings: list[MappingApproval]
    platform_id: int | None = None


# =========================================================
# RELIABLE CSV / EXCEL ORDER IMPORT
# =========================================================

def _import_orders_directly(db, dataframe, mappings, platform_name):
    """Deterministic order importer for CSV/Excel merchant data."""

    field_map = {}

    for item in mappings:
        source = item.get("source_column")
        target = item.get("target_field")
        if source and target and target != "ignore":
            field_map[target] = source

    def norm(value):
        return (
            str(value).strip().lower()
            .replace("_", " ")
            .replace("-", " ")
        )

    columns = list(dataframe.columns)
    normalized = {norm(c): c for c in columns}

    aliases = {
        "order_customer": [
            "customer", "customer name", "buyer", "buyer name"
        ],
        "customer_email": [
            "customer email", "email", "email address"
        ],
        "order_product": [
            "product", "product name", "item", "item name"
        ],
        "order_quantity": [
            "qty", "quantity", "order quantity"
        ],
        "order_total_amount": [
            "amount", "total", "total amount",
            "order amount", "order total", "price", "value"
        ],
        "order_created_at": [
            "date", "order date", "created at", "timestamp"
        ],
        "order_status": [
            "status", "order status"
        ],
        "order_payment_status": [
            "payment status", "payment"
        ],
    }

    for target, names in aliases.items():
        if target in field_map:
            continue
        for name in names:
            if norm(name) in normalized:
                field_map[target] = normalized[norm(name)]
                break

    def get(row, target):
        source = field_map.get(target)
        if not source or source not in row:
            return None

        value = row[source]
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass

        if isinstance(value, str):
            value = value.strip()

        return value if value != "" else None

    def money(value):
        if value is None:
            return 0.0
        try:
            return float(
                str(value)
                .replace("₹", "")
                .replace("$", "")
                .replace("€", "")
                .replace(",", "")
                .strip()
            )
        except Exception:
            return 0.0

    def qty(value):
        if value is None:
            return 1
        try:
            return max(int(float(value)), 1)
        except Exception:
            return 1

    def find_customer(customer_value, email=None):
        if email:
            email = str(email).strip()
            found = (
                db.query(Customer)
                .filter(Customer.email == email)
                .first()
            )
            if found:
                return found

        if customer_value:
            name = str(customer_value).strip()

            found = (
                db.query(Customer)
                .filter(Customer.name == name)
                .first()
            )
            if found:
                return found

            for customer in db.query(Customer).all():
                if (
                    customer.name
                    and customer.name.strip().lower()
                    == name.lower()
                ):
                    return customer

        return None

    def find_product(product_value):
        if not product_value:
            return None

        name = str(product_value).strip()

        found = (
            db.query(Product)
            .filter(Product.name == name)
            .first()
        )
        if found:
            return found

        for product in db.query(Product).all():
            if (
                product.name
                and product.name.strip().lower()
                == name.lower()
            ):
                return product

        return None

    from datetime import datetime

    imported = 0
    skipped = 0
    duplicates = 0

    for _, row in dataframe.iterrows():

        customer_value = get(row, "order_customer")
        email = get(row, "customer_email")
        product_value = get(row, "order_product")

        if not customer_value or not product_value:
            skipped += 1
            continue

        customer = find_customer(
            customer_value,
            email,
        )

        if not customer and email:
            customer = Customer(
                name=str(customer_value).strip(),
                email=str(email).strip(),
                phone="",
            )
            db.add(customer)
            db.flush()

        if not customer:
            skipped += 1
            continue

        product = find_product(product_value)

        if not product:
            product = Product(
                name=str(product_value).strip(),
                description="",
                price=money(get(row, "product_price")),
                inventory=0,
                category="",
            )
            db.add(product)
            db.flush()

        order_quantity = qty(
            get(row, "order_quantity")
        )
        amount = money(
            get(row, "order_total_amount")
        )

        date_value = get(
            row,
            "order_created_at",
        )

        if date_value is not None:
            try:
                created_at = pd.to_datetime(
                    date_value
                ).to_pydatetime()
            except Exception:
                created_at = datetime.utcnow()
        else:
            created_at = datetime.utcnow()

        duplicate_query = (
            db.query(Order)
            .filter(
                Order.customer_id == customer.id,
                Order.product_id == product.id,
                Order.quantity == order_quantity,
                Order.total_amount == amount,
            )
        )

        if hasattr(Order, "platform"):
            duplicate_query = duplicate_query.filter(
                Order.platform == platform_name
            )

        if duplicate_query.first():
            duplicates += 1
            continue

        order_data = {
            "customer_id": customer.id,
            "product_id": product.id,
            "quantity": order_quantity,
            "total_amount": amount,
            "created_at": created_at,
        }

        if hasattr(Order, "platform"):
            order_data["platform"] = platform_name

        order = Order(**order_data)

        status = get(row, "order_status")
        if status and hasattr(order, "status"):
            order.status = str(status)

        payment_status = get(
            row,
            "order_payment_status",
        )
        if payment_status and hasattr(
            order,
            "payment_status",
        ):
            order.payment_status = str(
                payment_status
            )

        db.add(order)

        customer.total_orders = (
            customer.total_orders or 0
        ) + 1

        customer.total_spent = (
            customer.total_spent or 0
        ) + amount

        imported += 1

    db.commit()

    return {
        "success": True,
        "imported": imported,
        "orders_imported": imported,
        "duplicates": duplicates,
        "skipped": skipped,
    }


# =========================================================
# AUTOMATIC REVENUE OPPORTUNITY ACTIVATION
# =========================================================

def _activate_revenue_opportunities(db: Session):
    """
    Immediately turn imported purchase history into a real MUNEEM
    cross-sell opportunity and an action-queue item.

    This is deterministic and does not depend on Gemini being available.
    """

    products = db.query(Product).all()

    if len(products) < 2:
        return []

    # Build customer -> purchased product IDs.
    customer_products = {}

    for order in db.query(Order).all():
        if order.customer_id and order.product_id:
            customer_products.setdefault(
                order.customer_id,
                set(),
            ).add(order.product_id)

    if not customer_products:
        return []

    # Count product co-occurrence across customers.
    pair_count = {}

    for purchased in customer_products.values():
        purchased = list(purchased)

        for source_id in purchased:
            for related_id in purchased:
                if source_id == related_id:
                    continue

                key = (source_id, related_id)
                pair_count[key] = (
                    pair_count.get(key, 0) + 1
                )

    # Pick the strongest observed product relationship.
    ranked_pairs = sorted(
        pair_count.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    for (source_id, related_id), affinity_count in ranked_pairs:

        source_product = (
            db.query(Product)
            .filter(Product.id == source_id)
            .first()
        )

        related_product = (
            db.query(Product)
            .filter(Product.id == related_id)
            .first()
        )

        if not source_product or not related_product:
            continue

        # Customers who bought source but not related.
        target_customers = [
            customer_id
            for customer_id, purchased in customer_products.items()
            if source_id in purchased
            and related_id not in purchased
        ]

        if not target_customers:
            continue

        # Avoid creating the same opportunity repeatedly.
        existing = (
            db.query(Opportunity)
            .filter(
                Opportunity.opportunity_type == "cross_sell",
                Opportunity.product_id == source_id,
                Opportunity.related_product_id == related_id,
            )
            .first()
        )

        if existing:
            opportunity = existing
            opportunity.customer_count = len(
                target_customers
            )
            opportunity.estimated_value = (
                float(related_product.price or 0)
                * len(target_customers)
            )
        else:
            opportunity = Opportunity(
                opportunity_type="cross_sell",
                product_id=source_id,
                related_product_id=related_id,
                title=(
                    f"{len(target_customers)} customers "
                    f"who bought {source_product.name} "
                    f"may also buy {related_product.name}"
                ),
                description=(
                    f"MUNEEM found a purchase pattern: "
                    f"customers buying {source_product.name} "
                    f"also purchase {related_product.name}. "
                    f"{len(target_customers)} customers have "
                    f"not purchased the complementary product yet."
                ),
                customer_count=len(target_customers),
                estimated_value=(
                    float(related_product.price or 0)
                    * len(target_customers)
                ),
                confidence="High",
            )

            db.add(opportunity)
            db.flush()


        db.commit()

        return [opportunity]

    return []


# =========================================================
# UPLOAD DATA
# =========================================================


@router.post("/upload")
async def upload_data(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is required.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    try:

        result = data_ingestion_service.read_file(
            filename=file.filename,
            content=content,
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Could not read file: {str(e)}",
        )

    if not result["valid"]:

        raise HTTPException(
            status_code=400,
            detail=result["message"],
        )

    file_type = result["file_type"]

    # =====================================================
    # CSV / EXCEL
    # =====================================================

    if file_type in {"csv", "excel"}:

        dataframe = result["dataframe"]

        if dataframe.empty:

            raise HTTPException(
                status_code=400,
                detail=(
                    "The uploaded file contains "
                    "no data."
                ),
            )

        inspection = (
            data_ingestion_service.inspect_dataframe(
                dataframe
            )
        )

        try:

            mapping = (
                data_mapping_service.generate_mapping(
                    columns=inspection["columns"],
                    sample_rows=inspection["preview"],
                )
            )

        except Exception as e:

            # This should rarely be reached because
            # data_mapping_service now has a local
            # fallback. It remains here as a final
            # safety boundary.

            raise HTTPException(
                status_code=500,
                detail=(
                    "Data mapping failed: "
                    f"{str(e)}"
                ),
            )

        upload_id = (
            upload_session_service.create_session(
                filename=file.filename,
                file_type=file_type,
                data=dataframe,
            )
        )

        return {
            "success": True,
            "upload_id": upload_id,
            "filename": file.filename,
            "file_type": file_type,
            "data": inspection,
            "ai_mapping": mapping.model_dump(),
            "requires_confirmation": True,
            "message": (
                "File analyzed successfully. "
                "Review the mapping before importing."
            ),
        }

    # =====================================================
    # PDF
    # =====================================================

    if file_type == "pdf":

        pdf_text = result["text"]
        pdf_pages = result["pages"]

        if not pdf_text.strip():

            raise HTTPException(
                status_code=400,
                detail=(
                    "The PDF does not contain "
                    "extractable text."
                ),
            )

        inspection = (
            data_ingestion_service.inspect_pdf(
                text=pdf_text,
                pages=pdf_pages,
            )
        )

        try:

            mapping = (
                data_mapping_service
                .generate_mapping_from_pdf(
                    text=pdf_text
                )
            )

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=(
                    "PDF analysis failed: "
                    f"{str(e)}"
                ),
            )

        upload_id = (
            upload_session_service.create_session(
                filename=file.filename,
                file_type=file_type,
                data={
                    "text": pdf_text,
                    "pages": pdf_pages,
                },
            )
        )

        return {
            "success": True,
            "upload_id": upload_id,
            "filename": file.filename,
            "file_type": "pdf",
            "data": inspection,
            "ai_mapping": mapping.model_dump(),
            "requires_confirmation": True,
            "message": (
                "PDF analyzed successfully. "
                "Review the mapping before importing."
            ),
        }

    # =====================================================
    # UNSUPPORTED FILE
    # =====================================================

    raise HTTPException(
        status_code=400,
        detail="Unsupported file type.",
    )


# =========================================================
# GET UPLOAD SESSION
# =========================================================


@router.get("/upload/{upload_id}")
async def get_upload(
    upload_id: str,
):

    session = (
        upload_session_service.get_session(
            upload_id
        )
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail="Upload session not found.",
        )

    return {
        "success": True,
        "upload_id": upload_id,
        "filename": session["filename"],
        "file_type": session["file_type"],
    }


# =========================================================
# CONFIRM AND IMPORT
# =========================================================


@router.post(
    "/upload/{upload_id}/confirm"
)
async def confirm_upload(
    upload_id: str,
    request: ImportConfirmation,
    db: Session = Depends(get_db),
):

    # -----------------------------------------------------
    # FIND UPLOAD SESSION
    # -----------------------------------------------------

    session = (
        upload_session_service.get_session(
            upload_id
        )
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail="Upload session not found.",
        )

    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    if session["file_type"] == "pdf":

        raise HTTPException(
            status_code=400,
            detail=(
                "PDF import is not enabled yet. "
                "PDF analysis is working, but "
                "structured table normalization "
                "must be completed before import."
            ),
        )

    # -----------------------------------------------------
    # RESOLVE PLATFORM
    # -----------------------------------------------------

    platform_name = "direct"

    if request.platform_id is not None:

        platform = (
            db.query(Platform)
            .filter(
                Platform.id
                == request.platform_id
            )
            .first()
        )

        if not platform:

            raise HTTPException(
                status_code=404,
                detail="Selected platform not found.",
            )

        if not platform.is_active:

            raise HTTPException(
                status_code=400,
                detail=(
                    "The selected platform is not "
                    "currently connected."
                ),
            )

        platform_name = (
            platform.name
            or platform.display_name
            or "direct"
        )

        platform_name = (
            str(platform_name)
            .strip()
            .lower()
        )

    # -----------------------------------------------------
    # GET DATAFRAME
    # -----------------------------------------------------

    dataframe = session["data"]

    if dataframe is None or dataframe.empty:

        raise HTTPException(
            status_code=400,
            detail="Uploaded dataset is empty.",
        )

    # -----------------------------------------------------
    # CONVERT MAPPINGS
    # -----------------------------------------------------

    mappings = [
        mapping.model_dump()
        for mapping in request.mappings
    ]

    # -----------------------------------------------------
    # VALID DATASET TYPES
    # -----------------------------------------------------

    allowed_dataset_types = {
        "customers",
        "products",
        "orders",
        "transactions",
        "mixed",
        "unknown",
    }

    if request.dataset_type not in allowed_dataset_types:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid dataset type: "
                f"{request.dataset_type}"
            ),
        )

    # -----------------------------------------------------
    # VALID SOURCE COLUMNS
    # -----------------------------------------------------

    valid_columns = set(
        dataframe.columns
    )

    for mapping in mappings:

        source_column = (
            mapping["source_column"]
        )

        if source_column not in valid_columns:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Unknown source column: "
                    f"{source_column}"
                ),
            )

    # -----------------------------------------------------
    # VALID TARGET FIELDS
    # -----------------------------------------------------

    allowed_target_fields = {
        "customer_name",
        "customer_email",
        "customer_phone",

        "product_name",
        "product_description",
        "product_price",
        "product_inventory",
        "product_category",

        "order_customer",
        "order_product",
        "order_quantity",
        "order_total_amount",
        "order_status",
        "order_payment_status",
        "order_created_at",

        "transaction_order",
        "transaction_amount",
        "transaction_payment_method",
        "transaction_status",
        "transaction_payment_id",
        "transaction_created_at",

        "ignore",
    }

    for mapping in mappings:

        target_field = (
            mapping["target_field"]
        )

        if target_field not in allowed_target_fields:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid target field: "
                    f"{target_field}"
                ),
            )

    # -----------------------------------------------------
    # PREVENT EXACT DUPLICATE MAPPINGS
    # -----------------------------------------------------

    mapping_pairs = set()

    for mapping in mappings:

        pair = (
            mapping["source_column"],
            mapping["target_field"],
        )

        if pair in mapping_pairs:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Duplicate field mapping: "
                    f"{mapping['source_column']} "
                    "→ "
                    f"{mapping['target_field']}"
                ),
            )

        mapping_pairs.add(pair)

    # -----------------------------------------------------
    # REQUIRE AT LEAST ONE MAPPING
    # -----------------------------------------------------

    if not mappings:

        raise HTTPException(
            status_code=400,
            detail=(
                "At least one field mapping "
                "is required."
            ),
        )

    # -----------------------------------------------------
    # IMPORT DATA
    # -----------------------------------------------------

    try:

        # Force real order-shaped CSV/Excel files through the deterministic
        # order importer even if AI classified them as transactions/mixed.
        normalized_columns = {
            str(column).strip().lower().replace("_", " ")
            for column in dataframe.columns
        }

        order_signals = {
            "customer",
            "customer name",
            "buyer",
            "product",
            "product name",
            "item",
            "qty",
            "quantity",
            "amount",
            "total",
            "total amount",
        }

        looks_like_orders = (
            len(normalized_columns.intersection(order_signals))
            >= 3
        )

        if (
            request.dataset_type in {"orders", "mixed"}
            or looks_like_orders
        ):
            result = _import_orders_directly(
                db=db,
                dataframe=dataframe,
                mappings=mappings,
                platform_name=platform_name,
            )
        else:
            result = data_import_service.import_data(
                db=db,
                dataframe=dataframe,
                mappings=mappings,
                dataset_type=request.dataset_type,
                platform=platform_name,
            )

    except Exception as e:

        db.rollback()

        print("\n" + "=" * 70)
        print("MUNEEM DATA IMPORT ERROR")
        print("=" * 70)
        print(f"ERROR TYPE: {type(e).__name__}")
        print(f"ERROR: {str(e)}")
        print("=" * 70 + "\n")

        raise HTTPException(
            status_code=500,
            detail=(
                "Data import failed: "
                f"{type(e).__name__}: {str(e)}"
            ),
        )

    # -----------------------------------------------------
    # IMPORT SERVICE REJECTED
    # -----------------------------------------------------

    if not result["success"]:

        raise HTTPException(
            status_code=400,
            detail=result["message"],
        )

    # -----------------------------------------------------
    # DETECT REVENUE OPPORTUNITIES
    # -----------------------------------------------------

    try:

        opportunities = (
            detect_cross_sell_opportunities(
                db
            )
        )

    except Exception as e:

        opportunities = []

        print(
            "Opportunity detection failed: "
            f"{str(e)}"
        )

    # If the AI/legacy detector returns nothing, activate the merchant's
    # imported purchase patterns immediately using deterministic logic.
    if not opportunities:

        try:
            opportunities = _activate_revenue_opportunities(db)
        except Exception as e:
            db.rollback()
            opportunities = []

            print(
                "Automatic opportunity activation failed: "
                f"{type(e).__name__}: {str(e)}"
            )

    # -----------------------------------------------------
    # MUNEEM REVENUE AGENT
    # -----------------------------------------------------
    # This runs AFTER the merchant data has been imported.
    # If the agent fails, the successful import is preserved.

    # Pass the exact confirmed upload into the agent as runtime
    # context. SQLite remains the persistent source of truth.
    upload_context = {
        "filename": session["filename"],
        "platform": platform_name,
        "dataset_type": request.dataset_type,
        "columns": [
            str(column)
            for column in dataframe.columns
        ],
        "mappings": mappings,
        # Bound the runtime payload; the complete dataset has
        # already gone through the normal import pipeline.
        "rows": dataframe.head(250).to_dict(
            orient="records"
        ),
        "row_count": int(len(dataframe)),
    }

    agent_result = None

    try:
        agent_result = run_revenue_agent(
            db=db,
            upload_context=upload_context,
        )

        print(
            "MUNEEM Revenue Agent:",
            agent_result,
        )

    except Exception as agent_error:

        db.rollback()

        agent_result = {
            "status": "skipped",
            "reason": str(agent_error),
            "opportunities_created": 0,
            "actions_created": 0,
        }

        print(
            "MUNEEM Revenue Agent skipped: "
            f"{type(agent_error).__name__}: "
            f"{str(agent_error)}"
        )

    # -----------------------------------------------------
    # DELETE TEMPORARY UPLOAD SESSION
    # -----------------------------------------------------

    upload_session_service.delete_session(
        upload_id
    )

    # -----------------------------------------------------
    # BUILD RESPONSE
    # -----------------------------------------------------

    response = {
        "success": True,

        "upload_id": upload_id,

        "filename": session["filename"],

        "dataset_type": request.dataset_type,

        "platform": platform_name,

        "import": {
            "imported": result.get(
                "imported",
                0,
            ),

            "skipped": result.get(
                "skipped",
                0,
            ),
        },

        "opportunities_detected": len(
            opportunities
        ),

        "agent": agent_result,

        "opportunities": [
            {
                "id": opportunity.id,

                "type": (
                    opportunity.opportunity_type
                ),

                "title": (
                    opportunity.title
                ),

                "description": (
                    opportunity.description
                ),

                "customer_count": (
                    opportunity.customer_count
                ),

                "estimated_value": (
                    opportunity.estimated_value
                ),

                "confidence": (
                    opportunity.confidence
                ),
            }

            for opportunity in opportunities
        ],

        "message": (
            "Merchant data imported successfully "
            f"from {platform_name} and revenue "
            "opportunities analyzed."
        ),
    }

    # -----------------------------------------------------
    # INCLUDE DETAILED COUNTS FOR MIXED DATA
    # -----------------------------------------------------

    if request.dataset_type == "mixed":

        response["import"].update(
            {
                "customers_imported": result.get(
                    "customers_imported",
                    0,
                ),

                "products_imported": result.get(
                    "products_imported",
                    0,
                ),

                "orders_imported": result.get(
                    "orders_imported",
                    0,
                ),

                "transactions_imported": result.get(
                    "transactions_imported",
                    0,
                ),
            }
        )

    return response