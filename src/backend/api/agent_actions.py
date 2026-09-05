from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.backend.database import get_db

from src.backend.models.customer import Customer
from src.backend.models.product import Product
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
def create_action(
    opportunity_id: int,
    db: Session = Depends(get_db),
):
    result = agent_action_service.create_action_from_opportunity(
        db=db,
        opportunity_id=opportunity_id,
    )

    if not result.get("success", False):
        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Unable to create agent action.",
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
    actions = agent_action_service.get_actions(db)

    enriched_actions = []

    for action in actions:

        customer = None
        product = None
        opportunity = None

        if getattr(action, "customer_id", None):
            customer = (
                db.query(Customer)
                .filter(Customer.id == action.customer_id)
                .first()
            )

        if getattr(action, "product_id", None):
            product = (
                db.query(Product)
                .filter(Product.id == action.product_id)
                .first()
            )

        if getattr(action, "opportunity_id", None):
            opportunity = (
                db.query(Opportunity)
                .filter(
                    Opportunity.id == action.opportunity_id
                )
                .first()
            )

        final_amount = (
            action.final_amount
            if action.final_amount is not None
            else action.action_amount
        )

        enriched_actions.append(
            {
                "id": action.id,
                "opportunity_id": action.opportunity_id,
                "action_type": action.action_type,
                "action_amount": action.action_amount,
                "status": action.status,
                "approval_required": bool(
                    action.approval_required
                ),

                "customer": (
                    {
                        "id": customer.id,
                        "name": customer.name,
                        "email": customer.email,
                    }
                    if customer
                    else None
                ),

                "product": (
                    {
                        "id": product.id,
                        "name": product.name,
                        "price": product.price,
                    }
                    if product
                    else None
                ),

                "offer": {
                    "original_amount": (
                        action.original_amount
                    ),
                    "discount_percentage": (
                        action.discount_percentage or 0
                    ),
                    "discount_amount": (
                        action.discount_amount or 0
                    ),
                    "final_amount": final_amount,
                },

                "customer_message": action.customer_message,

                "execution_result": action.execution_result,

                "created_at": action.created_at,
                "updated_at": action.updated_at,

                "opportunity": (
                    {
                        "title": opportunity.title,
                        "description": opportunity.description,
                    }
                    if opportunity
                    else None
                ),
            }
        )

    return enriched_actions


# =========================================================
# GET ONE ACTION
# =========================================================

@router.get("/{action_id}")
def get_action(
    action_id: int,
    db: Session = Depends(get_db),
):
    action = agent_action_service.get_action(
        db=db,
        action_id=action_id,
    )

    if not action:
        raise HTTPException(
            status_code=404,
            detail="Agent action not found.",
        )

    customer = None
    product = None
    opportunity = None

    if getattr(action, "customer_id", None):
        customer = (
            db.query(Customer)
            .filter(Customer.id == action.customer_id)
            .first()
        )

    if getattr(action, "product_id", None):
        product = (
            db.query(Product)
            .filter(Product.id == action.product_id)
            .first()
        )

    if getattr(action, "opportunity_id", None):
        opportunity = (
            db.query(Opportunity)
            .filter(
                Opportunity.id == action.opportunity_id
            )
            .first()
        )

    final_amount = (
        action.final_amount
        if action.final_amount is not None
        else action.action_amount
    )

    return {
        "id": action.id,
        "opportunity_id": action.opportunity_id,
        "action_type": action.action_type,
        "action_amount": action.action_amount,
        "status": action.status,
        "approval_required": bool(
            action.approval_required
        ),

        "customer": (
            {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
            }
            if customer
            else None
        ),

        "product": (
            {
                "id": product.id,
                "name": product.name,
                "price": product.price,
            }
            if product
            else None
        ),

        "offer": {
            "original_amount": action.original_amount,
            "discount_percentage": (
                action.discount_percentage or 0
            ),
            "discount_amount": (
                action.discount_amount or 0
            ),
            "final_amount": final_amount,
        },

        "customer_message": action.customer_message,
        "execution_result": action.execution_result,
        "created_at": action.created_at,
        "updated_at": action.updated_at,

        "opportunity": (
            {
                "title": opportunity.title,
                "description": opportunity.description,
            }
            if opportunity
            else None
        ),
    }


# =========================================================
# APPROVE ACTION
# =========================================================

@router.post("/{action_id}/approve")
def approve_action(
    action_id: int,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # 1. Record merchant approval.
    # -----------------------------------------------------

    approval_result = agent_action_service.approve_action(
        db=db,
        action_id=action_id,
    )

    if not approval_result.get("success", False):
        raise HTTPException(
            status_code=400,
            detail=approval_result.get(
                "message",
                "Unable to approve agent action.",
            ),
        )

    # -----------------------------------------------------
    # 2. Reload the action so ActionExecutor gets the latest
    #    database state.
    # -----------------------------------------------------

    action = agent_action_service.get_action(
        db=db,
        action_id=action_id,
    )

    if not action:
        raise HTTPException(
            status_code=404,
            detail="Approved agent action could not be found.",
        )

    # -----------------------------------------------------
    # 3. Execute exactly once:
    #
    #    Razorpay → payment record → email → execution_result
    # -----------------------------------------------------

    execution_result = action_executor.execute(
        db=db,
        action=action,
    )

    # -----------------------------------------------------
    # 4. Return the real execution state.
    #
    #    Do NOT report approval as final success if execution
    #    failed.
    # -----------------------------------------------------

    if not execution_result.get("success", False):

        # Keep the useful backend error visible to Swagger/UI.
        status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=execution_result.get(
                "message",
                "Agent action execution failed.",
            ),
        )

    return {
        "success": True,
        "action_id": action_id,
        "status": execution_result.get(
            "status",
            "executed",
        ),
        "approval": approval_result,
        "execution": execution_result,
        "razorpay": execution_result.get("razorpay"),
        "payment_link": execution_result.get("payment_link"),
        "payment_id": execution_result.get("payment_id"),
        "email": execution_result.get("email"),
        "offer": execution_result.get("offer"),
        "purchase_history": execution_result.get(
            "purchase_history",
            [],
        ),
        "message": execution_result.get(
            "message",
            "Action approved and executed successfully.",
        ),
    }


# =========================================================
# REJECT ACTION
# =========================================================

@router.post("/{action_id}/reject")
def reject_action(
    action_id: int,
    db: Session = Depends(get_db),
):
    result = agent_action_service.reject_action(
        db=db,
        action_id=action_id,
    )

    if not result.get("success", False):
        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Unable to reject agent action.",
            ),
        )

    return result


# =========================================================
# EXECUTE ACTION
# =========================================================

@router.post("/{action_id}/execute")
def execute_action(
    action_id: int,
    db: Session = Depends(get_db),
):
    action = agent_action_service.get_action(
        db=db,
        action_id=action_id,
    )

    if not action:
        raise HTTPException(
            status_code=404,
            detail="Agent action not found.",
        )

    result = action_executor.execute(
        db=db,
        action=action,
    )

    if not result.get("success", False):
        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Agent action execution failed.",
            ),
        )

    return result
