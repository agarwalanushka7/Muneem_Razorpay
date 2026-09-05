from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.backend.database import get_db

from src.backend.models.customer import Customer
from src.backend.models.product import Product
from src.backend.models.order import Order
from src.backend.models.opportunity import Opportunity

from src.backend.services.agent_action_service import (
    agent_action_service,
)

from src.backend.services.action_executor import (
    action_executor,
)


router = APIRouter(
    prefix="/agent-actions",
    tags=["Agent Actions"],
)


# =========================================================
# CREATE ACTION
# =========================================================

@router.post("/create/{opportunity_id}")
def create_agent_action(
    opportunity_id: int,
    db: Session = Depends(get_db),
):
    result = (
        agent_action_service
        .create_action_from_opportunity(
            db=db,
            opportunity_id=opportunity_id,
        )
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Failed to create agent action.",
            ),
        )

    return result


# =========================================================
# GET ALL ACTIONS
# =========================================================

@router.get("/")
def get_actions(
    db: Session = Depends(get_db),
):
    actions = (
        agent_action_service
        .get_actions(db=db)
    )

    result = []

    for action in actions:

        # =================================================
        # CUSTOMER
        # =================================================

        customer = None

        if getattr(
            action,
            "customer_id",
            None,
        ):

            customer = (
                db.query(Customer)
                .filter(
                    Customer.id
                    == action.customer_id
                )
                .first()
            )

        # =================================================
        # PRODUCT
        # =================================================

        product = None

        if getattr(
            action,
            "product_id",
            None,
        ):

            product = (
                db.query(Product)
                .filter(
                    Product.id
                    == action.product_id
                )
                .first()
            )

        # =================================================
        # PREVIOUS PURCHASE HISTORY
        # =================================================

        purchase_history = []

        if customer:

            orders = (
                db.query(Order)
                .filter(
                    Order.customer_id
                    == customer.id
                )
                .order_by(
                    Order.created_at.desc()
                )
                .all()
            )

            for order in orders:

                purchased_product = None

                if getattr(
                    order,
                    "product_id",
                    None,
                ):

                    purchased_product = (
                        db.query(Product)
                        .filter(
                            Product.id
                            == order.product_id
                        )
                        .first()
                    )

                if not purchased_product:
                    continue

                purchase_history.append(
                    {
                        "order_id": order.id,

                        "product_id": (
                            purchased_product.id
                        ),

                        "product_name": (
                            purchased_product.name
                        ),

                        "quantity": (
                            getattr(
                                order,
                                "quantity",
                                1,
                            )
                            or 1
                        ),

                        "amount": float(
                            getattr(
                                order,
                                "total_amount",
                                0,
                            )
                            or 0
                        ),

                        "created_at": (
                            order.created_at
                        ),
                    }
                )

        # =================================================
        # ACTION
        # =================================================

        result.append(
            {
                "id": action.id,

                "opportunity_id": (
                    action.opportunity_id
                ),

                "action_type": (
                    action.action_type
                ),

                "action_amount": (
                    action.action_amount
                ),

                "original_amount": (
                    getattr(
                        action,
                        "original_amount",
                        None,
                    )
                ),

                "discount_percentage": (
                    getattr(
                        action,
                        "discount_percentage",
                        0,
                    )
                    or 0
                ),

                "discount_amount": (
                    getattr(
                        action,
                        "discount_amount",
                        0,
                    )
                    or 0
                ),

                "final_amount": (
                    getattr(
                        action,
                        "final_amount",
                        None,
                    )
                    if getattr(
                        action,
                        "final_amount",
                        None,
                    )
                    is not None
                    else action.action_amount
                ),

                "approval_required": bool(
                    action.approval_required
                ),

                "status": action.status,

                # =================================================
                # CUSTOMER
                # =================================================

                "customer": (
                    {
                        "id": customer.id,
                        "name": customer.name,
                        "email": customer.email,
                        "total_orders": (
                            getattr(
                                customer,
                                "total_orders",
                                0,
                            )
                            or 0
                        ),
                        "total_spent": float(
                            getattr(
                                customer,
                                "total_spent",
                                0,
                            )
                            or 0
                        ),
                    }
                    if customer
                    else None
                ),

                # =================================================
                # PURCHASE HISTORY
                # =================================================

                "purchase_history": (
                    purchase_history
                ),

                # =================================================
                # PRODUCT
                # =================================================

                "product": (
                    {
                        "id": product.id,
                        "name": product.name,
                        "price": float(
                            product.price or 0
                        ),
                    }
                    if product
                    else None
                ),

                # =================================================
                # OFFER
                # =================================================

                "offer": {
                    "original_amount": (
                        getattr(
                            action,
                            "original_amount",
                            None,
                        )
                    ),

                    "discount_percentage": (
                        getattr(
                            action,
                            "discount_percentage",
                            0,
                        )
                        or 0
                    ),

                    "discount_amount": (
                        getattr(
                            action,
                            "discount_amount",
                            0,
                        )
                        or 0
                    ),

                    "final_amount": (
                        getattr(
                            action,
                            "final_amount",
                            None,
                        )
                        if getattr(
                            action,
                            "final_amount",
                            None,
                        )
                        is not None
                        else action.action_amount
                    ),
                },

                # =================================================
                # MESSAGE
                # =================================================

                "customer_message": (
                    action.customer_message
                ),

                # =================================================
                # EXECUTION
                # =================================================

                "execution_result": (
                    action.execution_result
                ),

                "created_at": (
                    action.created_at
                ),

                "updated_at": (
                    action.updated_at
                ),
            }
        )

    return result


# =========================================================
# GET ONE ACTION
# =========================================================

@router.get("/{action_id}")
def get_action(
    action_id: int,
    db: Session = Depends(get_db),
):
    action = (
        agent_action_service
        .get_action(
            db=db,
            action_id=action_id,
        )
    )

    if not action:

        raise HTTPException(
            status_code=404,
            detail="Agent action not found.",
        )

    return action


# =========================================================
# APPROVE + AUTOMATICALLY SEND
# =========================================================

@router.post("/{action_id}/approve")
def approve_action(
    action_id: int,
    db: Session = Depends(get_db),
):
    """
    One-click merchant approval.

    Flow:

    1. Merchant approves MUNEEM offer.
    2. Razorpay payment link is created.
    3. Personalized email is sent automatically.
    4. Action becomes executed.
    """

    # =====================================================
    # 1. APPROVE
    # =====================================================

    approval_result = (
        agent_action_service
        .approve_action(
            db=db,
            action_id=action_id,
        )
    )

    if not approval_result.get(
        "success",
        False,
    ):

        raise HTTPException(
            status_code=400,
            detail=approval_result.get(
                "message",
                "Failed to approve action.",
            ),
        )

    # =====================================================
    # 2. GET UPDATED ACTION
    # =====================================================

    action = (
        agent_action_service
        .get_action(
            db=db,
            action_id=action_id,
        )
    )

    if not action:

        raise HTTPException(
            status_code=404,
            detail="Approved action not found.",
        )

    # =====================================================
    # 3. CREATE RAZORPAY + SEND EMAIL
    # =====================================================

    execution_result = (
        action_executor.execute(
            db=db,
            action=action,
        )
    )

    if not execution_result.get(
        "success",
        False,
    ):

        return {
            "success": False,

            "action_id": action_id,

            "approval": approval_result,

            "execution": execution_result,

            "razorpay": execution_result.get(
                "razorpay"
            ),

            "email": execution_result.get(
                "email"
            ),

            "offer": execution_result.get(
                "offer"
            ),

            "message": execution_result.get(
                "message",
                "Offer approved but execution failed.",
            ),
        }

    # =====================================================
    # 4. SUCCESS
    # =====================================================

    return {
        "success": True,

        "action_id": action_id,

        "status": "executed",

        "approval": approval_result,

        "execution": execution_result,

        "razorpay": execution_result.get(
            "razorpay"
        ),

        "email": execution_result.get(
            "email"
        ),

        "offer": execution_result.get(
            "offer"
        ),

        "purchase_history": execution_result.get(
            "purchase_history",
            [],
        ),

        "message": (
            "Offer approved, Razorpay payment link "
            "created, and personalized email sent "
            "successfully."
        ),
    }


# =========================================================
# REJECT
# =========================================================

@router.post("/{action_id}/reject")
def reject_action(
    action_id: int,
    db: Session = Depends(get_db),
):
    result = (
        agent_action_service
        .reject_action(
            db=db,
            action_id=action_id,
        )
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Failed to reject action.",
            ),
        )

    return result


# =========================================================
# EXECUTE
# =========================================================
# Kept for existing functionality.
# APPROVE & SEND already executes automatically.
# =========================================================

@router.post("/{action_id}/execute")
def execute_action(
    action_id: int,
    db: Session = Depends(get_db),
):
    action = (
        agent_action_service
        .get_action(
            db=db,
            action_id=action_id,
        )
    )

    if not action:

        raise HTTPException(
            status_code=404,
            detail="Agent action not found.",
        )

    result = (
        action_executor.execute(
            db=db,
            action=action,
        )
    )

    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Failed to execute action.",
            ),
        )

    return result