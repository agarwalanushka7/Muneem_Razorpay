from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.backend.database import get_db

from src.backend.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
)

from src.backend.repositories.customer_repository import (
    get_all_customers,
    get_customer_by_id,
    get_customer_by_email,
    create_customer,
    update_customer,
    delete_customer,
)

from src.backend.models.customer import Customer
from src.backend.models.order import Order
from src.backend.models.product import Product
from src.backend.models.opportunity import Opportunity
from src.backend.models.agent_action import AgentAction


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


# =========================================================
# GET ALL CUSTOMERS
# =========================================================

@router.get(
    "/",
    response_model=list[CustomerResponse],
)
def read_customers(
    db: Session = Depends(get_db),
):
    return get_all_customers(db)


# =========================================================
# CUSTOMER INTELLIGENCE
# IMPORTANT:
# This MUST come before /{customer_id}
# =========================================================

@router.get("/intelligence")
def get_customer_intelligence(
    db: Session = Depends(get_db),
):
    """
    Returns dynamic customer intelligence based on:

    Customers
    Orders
    Products
    Opportunities
    Agent Actions

    No customer or product is hardcoded.
    """

    customers = (
        db.query(Customer)
        .order_by(Customer.id)
        .all()
    )

    customer_data = []

    for customer in customers:

        # -------------------------------------------------
        # ORDERS
        # -------------------------------------------------

        orders = (
            db.query(Order)
            .filter(
                Order.customer_id == customer.id
            )
            .order_by(
                desc(Order.created_at)
            )
            .all()
        )

        order_count = len(orders)

        # -------------------------------------------------
        # TOTAL SPENT
        # -------------------------------------------------

        total_spent = 0.0

        for order in orders:

            payment_status = (
                str(
                    order.payment_status or ""
                )
                .lower()
                .strip()
            )

            if payment_status in {
                "paid",
                "success",
                "successful",
                "completed",
                "captured",
            }:
                total_spent += float(
                    order.total_amount or 0
                )

        # Fallback to stored customer aggregate
        if (
            total_spent == 0
            and customer.total_spent
        ):
            total_spent = float(
                customer.total_spent
            )

        # -------------------------------------------------
        # RECENT PRODUCTS
        # -------------------------------------------------

        recent_products = []

        seen_products = set()

        for order in orders:

            if not order.product_id:
                continue

            if order.product_id in seen_products:
                continue

            product = (
                db.query(Product)
                .filter(
                    Product.id ==
                    order.product_id
                )
                .first()
            )

            if not product:
                continue

            recent_products.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "price": float(
                        product.price or 0
                    ),
                    "purchased_at": (
                        order.created_at.isoformat()
                        if order.created_at
                        else None
                    ),
                }
            )

            seen_products.add(
                product.id
            )

            if len(recent_products) >= 5:
                break

        # -------------------------------------------------
        # MUNEEM SIGNALS
        # -------------------------------------------------

        opportunity_rows = (
            db.query(
                Opportunity,
                AgentAction,
                Product,
            )
            .outerjoin(
                AgentAction,
                AgentAction.opportunity_id
                == Opportunity.id,
            )
            .outerjoin(
                Product,
                Product.id
                == Opportunity.related_product_id,
            )
            .filter(
                AgentAction.customer_id
                == customer.id
            )
            .order_by(
                desc(
                    Opportunity.created_at
                )
            )
            .all()
        )

        muneem_signals = []

        for (
            opportunity,
            action,
            recommended_product,
        ) in opportunity_rows:

            final_amount = None
            discount_percentage = 0.0
            action_status = None

            if action:

                final_amount = float(
                    action.final_amount
                    or action.action_amount
                    or 0
                )

                discount_percentage = float(
                    action.discount_percentage
                    or 0
                )

                action_status = (
                    action.status
                )

            else:

                final_amount = float(
                    opportunity.estimated_value
                    or 0
                )

            muneem_signals.append(
                {
                    "opportunity_id":
                        opportunity.id,

                    "type":
                        opportunity.opportunity_type,

                    "title":
                        opportunity.title,

                    "description":
                        opportunity.description,

                    "recommended_product":
                        (
                            {
                                "id":
                                    recommended_product.id,

                                "name":
                                    recommended_product.name,

                                "price":
                                    float(
                                        recommended_product.price
                                        or 0
                                    ),
                            }
                            if recommended_product
                            else None
                        ),

                    "estimated_value":
                        float(
                            opportunity.estimated_value
                            or 0
                        ),

                    "confidence":
                        opportunity.confidence,

                    "opportunity_status":
                        opportunity.status,

                    "action_status":
                        action_status,

                    "final_amount":
                        final_amount,

                    "discount_percentage":
                        discount_percentage,
                }
            )

        # -------------------------------------------------
        # CUSTOMER RESPONSE
        # -------------------------------------------------

        customer_data.append(
            {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,

                "orders": order_count,

                "total_spent": round(
                    total_spent,
                    2,
                ),

                "recent_products":
                    recent_products,

                "muneem_signals":
                    muneem_signals,
            }
        )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    total_customers = len(
        customer_data
    )

    total_orders = sum(
        customer["orders"]
        for customer in customer_data
    )

    total_customer_revenue = round(
        sum(
            customer["total_spent"]
            for customer in customer_data
        ),
        2,
    )

    customers_with_signals = sum(
        1
        for customer in customer_data
        if customer["muneem_signals"]
    )

    return {
        "summary": {
            "total_customers":
                total_customers,

            "total_orders":
                total_orders,

            "total_customer_revenue":
                total_customer_revenue,

            "customers_with_muneem_signals":
                customers_with_signals,
        },

        "customers":
            customer_data,
    }


# =========================================================
# GET SINGLE CUSTOMER
# IMPORTANT:
# This comes AFTER /intelligence
# =========================================================

@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def read_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    customer = get_customer_by_id(
        db,
        customer_id,
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return customer


# =========================================================
# CREATE CUSTOMER
# =========================================================

@router.post(
    "/",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
):
    existing_customer = (
        get_customer_by_email(
            db,
            customer_data.email,
        )
    )

    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists",
        )

    return create_customer(
        db=db,
        name=customer_data.name,
        email=customer_data.email,
        phone=customer_data.phone,
    )


# =========================================================
# UPDATE CUSTOMER
# =========================================================

@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def update_existing_customer(
    customer_id: int,
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
):
    customer = get_customer_by_id(
        db,
        customer_id,
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    existing_customer = (
        get_customer_by_email(
            db,
            customer_data.email,
        )
    )

    if (
        existing_customer
        and existing_customer.id
        != customer_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Another customer already uses this email",
        )

    return update_customer(
        db=db,
        customer=customer,
        name=customer_data.name,
        email=customer_data.email,
        phone=customer_data.phone,
    )


# =========================================================
# DELETE CUSTOMER
# =========================================================

@router.delete(
    "/{customer_id}"
)
def delete_existing_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    customer = get_customer_by_id(
        db,
        customer_id,
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    delete_customer(
        db,
        customer,
    )

    return {
        "message":
            "Customer deleted successfully"
    }