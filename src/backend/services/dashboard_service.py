from sqlalchemy.orm import Session
from sqlalchemy import func

from src.backend.models.customer import Customer
from src.backend.models.product import Product
from src.backend.models.order import Order
from src.backend.models.transaction import Transaction
from src.backend.models.opportunity import Opportunity
from src.backend.models.agent_action import AgentAction


class DashboardService:

    def get_dashboard_summary(
        self,
        db: Session,
    ):
        # ---------------------------------------------
        # BASIC COUNTS
        # ---------------------------------------------

        customer_count = (
            db.query(func.count(Customer.id))
            .scalar()
            or 0
        )

        product_count = (
            db.query(func.count(Product.id))
            .scalar()
            or 0
        )

        order_count = (
            db.query(func.count(Order.id))
            .scalar()
            or 0
        )

        transaction_count = (
            db.query(func.count(Transaction.id))
            .scalar()
            or 0
        )

        # ---------------------------------------------
        # REVENUE
        # ---------------------------------------------

        total_revenue = (
            db.query(
                func.coalesce(
                    func.sum(Order.total_amount),
                    0,
                )
            )
            .scalar()
            or 0
        )

        # ---------------------------------------------
        # OPPORTUNITIES
        # ---------------------------------------------

        opportunity_count = (
            db.query(
                func.count(Opportunity.id)
            )
            .scalar()
            or 0
        )

        open_opportunity_count = (
            db.query(
                func.count(Opportunity.id)
            )
            .filter(
                Opportunity.status != "closed"
            )
            .scalar()
            or 0
        )

        # ---------------------------------------------
        # AGENT ACTIONS
        # ---------------------------------------------

        action_count = (
            db.query(
                func.count(AgentAction.id)
            )
            .scalar()
            or 0
        )

        executed_action_count = (
            db.query(
                func.count(AgentAction.id)
            )
            .filter(
                AgentAction.status == "EXECUTED"
            )
            .scalar()
            or 0
        )

        approval_count = (
            db.query(
                func.count(AgentAction.id)
            )
            .filter(
                AgentAction.approval_required == 1
            )
            .scalar()
            or 0
        )

        # ---------------------------------------------
        # RECENT OPPORTUNITIES
        # ---------------------------------------------

        opportunities = (
            db.query(Opportunity)
            .order_by(
                Opportunity.id.desc()
            )
            .limit(10)
            .all()
        )

        opportunity_data = []

        for opportunity in opportunities:

            opportunity_data.append(
                {
                    "id": opportunity.id,
                    "type": (
                        opportunity.opportunity_type
                    ),
                    "title": opportunity.title,
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
                    "status": opportunity.status,
                    "created_at": (
                        opportunity.created_at
                    ),
                }
            )

        # ---------------------------------------------
        # RECENT ACTIONS
        # ---------------------------------------------

        actions = (
            db.query(AgentAction)
            .order_by(
                AgentAction.id.desc()
            )
            .limit(10)
            .all()
        )

        action_data = []

        for action in actions:

            action_data.append(
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
                    "approval_required": (
                        bool(
                            action.approval_required
                        )
                    ),
                    "status": action.status,
                    "execution_result": (
                        action.execution_result
                    ),
                }
            )

        # ---------------------------------------------
        # FINAL RESPONSE
        # ---------------------------------------------

        return {
            "success": True,

            "metrics": {
                "total_revenue": float(
                    total_revenue
                ),
                "customers": customer_count,
                "products": product_count,
                "orders": order_count,
                "transactions": (
                    transaction_count
                ),
                "opportunities": (
                    opportunity_count
                ),
                "open_opportunities": (
                    open_opportunity_count
                ),
                "agent_actions": action_count,
                "executed_actions": (
                    executed_action_count
                ),
                "approval_required": (
                    approval_count
                ),
            },

            "opportunities": (
                opportunity_data
            ),

            "recent_actions": (
                action_data
            ),
        }


dashboard_service = DashboardService()