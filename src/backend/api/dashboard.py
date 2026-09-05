from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.backend.database import get_db
from src.backend.models.order import Order
from src.backend.models.opportunity import Opportunity
from src.backend.models.agent_action import AgentAction
from src.backend.models.payment import Payment


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # Existing business revenue
    # -----------------------------------------------------

    total_revenue = float(
        db.query(
            func.coalesce(
                func.sum(Order.total_amount),
                0,
            )
        ).scalar()
        or 0
    )

    total_orders = int(
        db.query(
            func.count(Order.id)
        ).scalar()
        or 0
    )

    # -----------------------------------------------------
    # Opportunities
    # -----------------------------------------------------

    total_opportunity_value = float(
        db.query(
            func.coalesce(
                func.sum(Opportunity.estimated_value),
                0,
            )
        ).scalar()
        or 0
    )

    total_opportunities = int(
        db.query(
            func.count(Opportunity.id)
        ).scalar()
        or 0
    )

    # -----------------------------------------------------
    # Agent action states
    # -----------------------------------------------------

    pending_approvals = int(
        db.query(AgentAction)
        .filter(
            AgentAction.status == "pending_approval"
        )
        .count()
    )

    approved_actions = int(
        db.query(AgentAction)
        .filter(
            AgentAction.status == "approved"
        )
        .count()
    )

    executed_actions = int(
        db.query(AgentAction)
        .filter(
            AgentAction.status.in_(
                ["executed", "paid"]
            )
        )
        .count()
    )

    # -----------------------------------------------------
    # REAL MUNEEM REVENUE
    #
    # Revenue is based on Payment records.
    # Only successfully paid payments count.
    # -----------------------------------------------------

    paid_statuses = [
        "paid",
        "captured",
        "success",
        "successful",
        "completed",
    ]

    recovered_revenue = float(
        db.query(
            func.coalesce(
                func.sum(Payment.amount),
                0,
            )
        )
        .filter(
            Payment.status.in_(paid_statuses)
        )
        .scalar()
        or 0
    )

    recovered_count = int(
        db.query(Payment)
        .filter(
            Payment.status.in_(paid_statuses)
        )
        .count()
    )

    # -----------------------------------------------------
    # REAL PENDING MUNEEM REVENUE
    #
    # Payment links created but not yet paid.
    # -----------------------------------------------------

    pending_payment_statuses = [
        "created",
        "pending",
        "issued",
    ]

    pending_revenue = float(
        db.query(
            func.coalesce(
                func.sum(Payment.amount),
                0,
            )
        )
        .filter(
            Payment.status.in_(
                pending_payment_statuses
            )
        )
        .scalar()
        or 0
    )

    # -----------------------------------------------------
    # Recovery rate
    # -----------------------------------------------------

    recovery_rate = (
        recovered_revenue
        / total_opportunity_value
        * 100
        if total_opportunity_value > 0
        else 0.0
    )

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,

        "total_opportunities":
            total_opportunities,

        "total_opportunity_value":
            total_opportunity_value,

        "recovered_revenue":
            recovered_revenue,

        "recovered_count":
            recovered_count,

        "pending_revenue":
            pending_revenue,

        "recovery_rate":
            recovery_rate,

        "executed_actions":
            executed_actions,

        "pending_approvals":
            pending_approvals,

        "approved_actions":
            approved_actions,
    }