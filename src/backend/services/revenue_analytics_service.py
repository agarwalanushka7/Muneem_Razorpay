from sqlalchemy.orm import Session
from sqlalchemy import func

from src.backend.models.payment import Payment
from src.backend.models.opportunity import Opportunity
from src.backend.models.agent_action import AgentAction


class RevenueAnalyticsService:

    def get_dashboard_metrics(
        self,
        db: Session,
    ):
        # ---------------------------------------------
        # 1. TOTAL OPPORTUNITY VALUE
        # ---------------------------------------------

        total_opportunity_value = (
            db.query(
                func.coalesce(
                    func.sum(
                        Opportunity.estimated_value
                    ),
                    0,
                )
            )
            .scalar()
        )

        # ---------------------------------------------
        # 2. TOTAL RECOVERED REVENUE
        # ---------------------------------------------

        recovered_revenue = (
            db.query(
                func.coalesce(
                    func.sum(Payment.amount),
                    0,
                )
            )
            .filter(
                Payment.status == "paid"
            )
            .scalar()
        )

        # ---------------------------------------------
        # 3. PENDING PAYMENT VALUE
        # ---------------------------------------------

        pending_revenue = (
            db.query(
                func.coalesce(
                    func.sum(Payment.amount),
                    0,
                )
            )
            .filter(
                Payment.status == "created"
            )
            .scalar()
        )

        # ---------------------------------------------
        # 4. AI OPPORTUNITIES
        # ---------------------------------------------

        opportunity_count = (
            db.query(Opportunity)
            .count()
        )

        # ---------------------------------------------
        # 5. EXECUTED ACTIONS
        # ---------------------------------------------

        executed_actions = (
            db.query(AgentAction)
            .filter(
                AgentAction.status == "executed"
            )
            .count()
        )

        # ---------------------------------------------
        # 6. PENDING APPROVALS
        # ---------------------------------------------

        pending_approvals = (
            db.query(AgentAction)
            .filter(
                AgentAction.status
                == "pending_approval"
            )
            .count()
        )

        # ---------------------------------------------
        # 7. REVENUE AT RISK
        # ---------------------------------------------

        revenue_at_risk = (
            db.query(
                func.coalesce(
                    func.sum(
                        Opportunity.estimated_value
                    ),
                    0,
                )
            )
            .filter(
                Opportunity.status != "recovered"
            )
            .scalar()
        )

        # ---------------------------------------------
        # 8. RECOVERY RATE
        # ---------------------------------------------

        if revenue_at_risk > 0:
            recovery_rate = (
                recovered_revenue
                / revenue_at_risk
            ) * 100
        else:
            recovery_rate = 0

        return {
            "total_opportunity_value": float(
                total_opportunity_value or 0
            ),
            "recovered_revenue": float(
                recovered_revenue or 0
            ),
            "pending_revenue": float(
                pending_revenue or 0
            ),
            "revenue_at_risk": float(
                revenue_at_risk or 0
            ),
            "opportunity_count": opportunity_count,
            "executed_actions": executed_actions,
            "pending_approvals": pending_approvals,
            "recovery_rate": round(
                recovery_rate,
                2,
            ),
        }


revenue_analytics_service = (
    RevenueAnalyticsService()
)