from sqlalchemy.orm import Session

from src.backend.models.opportunity import Opportunity
from src.backend.models.customer import Customer
from src.backend.models.product import Product
from src.backend.models.agent_action import AgentAction

from src.backend.repositories.agent_action_repository import (
    create_agent_action,
    get_agent_action_by_id,
    get_agent_action_by_opportunity_and_customer,
    get_all_agent_actions,
    update_agent_action_status,
)

from src.backend.services.ai_policy_service import (
    ai_policy_service,
)

from src.backend.services.audit_service import (
    audit_service,
)

from src.backend.services.personalized_offer_service import (
    personalized_offer_service,
)


class AgentActionService:

    # =========================================================
    # CREATE ACTION FROM OPPORTUNITY
    # =========================================================

    def create_action_from_opportunity(
        self,
        db: Session,
        opportunity_id: int,
    ):
        opportunity = (
            db.query(Opportunity)
            .filter(Opportunity.id == opportunity_id)
            .first()
        )

        if not opportunity:
            return {
                "success": False,
                "message": "Opportunity not found.",
            }

        # IMPORTANT:
        # RevenueAgent is imported lazily here.
        # This prevents the circular import:
        # agent_action_service -> revenue_agent -> agent_action_service
        from src.backend.agents.revenue_agent import revenue_agent

        analysis = revenue_agent.analyze_opportunity(
            db=db,
            opportunity_id=opportunity_id,
        )

        if not analysis.get("success"):
            return {
                "success": False,
                "message": analysis.get(
                    "message",
                    "Revenue analysis failed.",
                ),
            }

        ai_decision = analysis.get("ai_decision", {})
        if not isinstance(ai_decision, dict):
            ai_decision = {}

        action_type = (
            ai_decision.get(
                "action",
                analysis.get("action_type", "no_action"),
            )
            or "no_action"
        )

        action_type = (
            str(action_type)
            .strip()
            .lower()
            .replace(" ", "_")
        )

        if opportunity.opportunity_type == "cross_sell":
            action_type = "cross_sell"

        if action_type in {
            "none",
            "do_nothing",
            "",
        }:
            action_type = "no_action"

        # -----------------------------------------------------
        # CUSTOMER
        # -----------------------------------------------------

        target_customer_id = (
            analysis.get("customer_id")
            or ai_decision.get("customer_id")
        )

        if not target_customer_id:
            investigation = analysis.get(
                "agent_investigation",
                analysis.get("investigation", {}),
            )

            if isinstance(investigation, dict):
                target_customer_id = (
                    investigation.get("customer_id")
                    or investigation.get("selected_customer_id")
                )

        if not target_customer_id and opportunity.opportunity_type == "cross_sell":
            # Fallback: choose the first customer associated
            # with the source product.
            source_product_id = getattr(
                opportunity,
                "product_id",
                None,
            )

            if source_product_id:
                from src.backend.models.order import Order

                source_order = (
                    db.query(Order)
                    .filter(Order.product_id == source_product_id)
                    .order_by(Order.id.desc())
                    .first()
                )

                if source_order:
                    target_customer_id = source_order.customer_id

        if not target_customer_id:
            return {
                "success": False,
                "message": (
                    "MUNEEM identified an opportunity but "
                    "could not identify the customer."
                ),
            }

        customer = (
            db.query(Customer)
            .filter(Customer.id == target_customer_id)
            .first()
        )

        if not customer:
            return {
                "success": False,
                "message": "The target customer could not be found.",
            }

        # -----------------------------------------------------
        # PRODUCT
        # -----------------------------------------------------

        target_product_id = (
            getattr(opportunity, "related_product_id", None)
            or analysis.get("product_id")
            or ai_decision.get("product_id")
        )

        if not target_product_id:
            return {
                "success": False,
                "message": (
                    "MUNEEM identified a customer opportunity "
                    "but could not identify the recommended product."
                ),
            }

        product = (
            db.query(Product)
            .filter(Product.id == target_product_id)
            .first()
        )

        if not product:
            return {
                "success": False,
                "message": "The recommended product could not be found.",
            }

        if (getattr(product, "inventory", 1) or 0) <= 0:
            return {
                "success": False,
                "message": f"{product.name} is currently out of stock.",
            }

        # -----------------------------------------------------
        # DUPLICATE PROTECTION
        # -----------------------------------------------------

        existing_action = (
            get_agent_action_by_opportunity_and_customer(
                db=db,
                opportunity_id=opportunity_id,
                customer_id=target_customer_id,
            )
        )

        if existing_action:
            return {
                "success": True,
                "existing": True,
                "action_id": existing_action.id,
                "opportunity_id": existing_action.opportunity_id,
                "action_type": existing_action.action_type,
                "action_amount": existing_action.action_amount,
                "status": existing_action.status,
                "approval_required": bool(
                    existing_action.approval_required
                ),
                "message": (
                    f"MUNEEM has already prepared an action "
                    f"for {customer.name}."
                ),
            }

        # -----------------------------------------------------
        # OFFER
        # -----------------------------------------------------

        offer_data = analysis.get("offer", {})
        if not isinstance(offer_data, dict):
            offer_data = {}

        merchant_policy = (
            ai_policy_service.get_or_create_policy(db)
        )

        discount_percentage = float(
            offer_data.get("discount_percentage", 0) or 0
        )

        if (
            opportunity.opportunity_type == "cross_sell"
            and discount_percentage <= 0
        ):
            discount_percentage = float(
                merchant_policy.get(
                    "max_discount_percentage",
                    0,
                )
                or 0
            )

        # Hard safety bound for merchant-controlled discounts.
        discount_percentage = max(
            0.0,
            min(10.0, discount_percentage),
        )

        offer_result = (
            personalized_offer_service.build_offer(
                db=db,
                customer_id=target_customer_id,
                product_id=target_product_id,
                discount_percentage=discount_percentage,
                reason=(
                    ai_decision.get("reason", "")
                    or analysis.get("reason", "")
                    or ""
                ),
            )
        )

        if not offer_result.get("success", False):
            return {
                "success": False,
                "message": offer_result.get(
                    "message",
                    "Could not prepare the personalized offer.",
                ),
            }

        original_amount = float(
            offer_result.get(
                "original_amount",
                product.price or 0,
            )
            or 0
        )

        discount_percentage = float(
            offer_result.get(
                "discount_percentage",
                discount_percentage,
            )
            or 0
        )

        discount_amount = float(
            offer_result.get("discount_amount", 0)
            or 0
        )

        final_amount = float(
            offer_result.get("final_amount", original_amount)
            or original_amount
        )

        customer_message = (
            offer_result.get("message")
            or (
                f"Hi {customer.name}, MUNEEM found a "
                f"personalized offer on {product.name} "
                f"based on your shopping activity."
            )
        )

        # -----------------------------------------------------
        # POLICY
        # -----------------------------------------------------

        policy_result = (
            ai_policy_service.evaluate_action(
                policy=merchant_policy,
                action_amount=final_amount,
                action_type=action_type,
                discount_percentage=discount_percentage,
                discount_amount=discount_amount,
            )
        )

        policy_allowed = bool(
            policy_result.get("allowed", False)
        )

        requires_approval = bool(
            policy_result.get("requires_approval", False)
        )

        if not policy_allowed or requires_approval:
            action_status = "pending_approval"
            approval_required = 1
        else:
            action_status = "auto_execute"
            approval_required = 0

        # -----------------------------------------------------
        # CREATE ACTION
        # -----------------------------------------------------

        action = create_agent_action(
            db=db,
            opportunity_id=opportunity.id,
            customer_id=customer.id,
            product_id=product.id,
            action_type=action_type,
            action_amount=final_amount,
            original_amount=original_amount,
            discount_percentage=discount_percentage,
            discount_amount=discount_amount,
            final_amount=final_amount,
            customer_message=customer_message,
            approval_required=approval_required,
            status=action_status,
        )

        audit_service.log(
            db=db,
            actor="MUNEEM",
            action="CREATE_AGENT_ACTION",
            entity_type="AGENT_ACTION",
            entity_id=action.id,
            status=action.status,
            details=(
                f"Prepared {action_type} offer for "
                f"{customer.name}: {product.name}. "
                f"Original ₹{original_amount:,.2f}; "
                f"discount {discount_percentage:g}%; "
                f"final ₹{final_amount:,.2f}."
            ),
        )

        db.commit()

        return {
            "success": True,
            "action_id": action.id,
            "opportunity_id": opportunity.id,
            "action_type": action.action_type,
            "status": action.status,
            "approval_required": bool(action.approval_required),
            "existing": False,
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
            },
            "product": {
                "id": product.id,
                "name": product.name,
                "price": original_amount,
            },
            "offer": {
                "original_amount": original_amount,
                "discount_percentage": discount_percentage,
                "discount_amount": discount_amount,
                "final_amount": final_amount,
            },
            "customer_message": customer_message,
            "ai_decision": {
                "action": action_type,
                "reason": ai_decision.get("reason", ""),
                "confidence": ai_decision.get("confidence"),
                "suggested_amount": ai_decision.get("suggested_amount"),
                "discount_percentage": discount_percentage,
                "expected_revenue_impact": ai_decision.get(
                    "expected_revenue_impact"
                ),
            },
            "policy": {
                "allowed": policy_allowed,
                "requires_approval": requires_approval,
                "reason": policy_result.get("reason", ""),
            },
            "message": (
                f"MUNEEM prepared a personalized "
                f"{product.name} offer for {customer.name}."
            ),
        }

    # =========================================================
    # GET ONE ACTION
    # =========================================================

    def get_action(
        self,
        db: Session,
        action_id: int,
    ):
        return get_agent_action_by_id(db, action_id)

    # =========================================================
    # GET ALL ACTIONS
    # =========================================================

    def get_actions(
        self,
        db: Session,
    ):
        return get_all_agent_actions(db)

    # =========================================================
    # APPROVE ACTION
    # =========================================================

    def approve_action(
        self,
        db: Session,
        action_id: int,
    ):
        action = get_agent_action_by_id(db, action_id)

        if not action:
            return {
                "success": False,
                "message": "Agent action not found.",
            }

        # A failed/approved action can be retried. The API route
        # is responsible for calling ActionExecutor exactly once.
        if action.status not in {
            "pending_approval",
            "approved",
            "failed",
        }:
            return {
                "success": False,
                "message": (
                    "Action cannot be approved from its current "
                    f"status: {action.status}."
                ),
            }

        # Only write a new approval/audit event when this is a
        # new approval or a retry of a failed execution.
        if action.status in {
            "pending_approval",
            "failed",
        }:
            update_agent_action_status(
                db=db,
                action=action,
                status="approved",
            )

            audit_service.log(
                db=db,
                actor="MERCHANT",
                action="APPROVE_AGENT_ACTION",
                entity_type="AGENT_ACTION",
                entity_id=action.id,
                status="approved",
                details=(
                    "Merchant approved the personalized "
                    "revenue action."
                ),
            )

            db.commit()

        return {
            "success": True,
            "action_id": action.id,
            "status": "approved",
            "message": "Revenue action approved successfully.",
        }

    # =========================================================
    # REJECT ACTION
    # =========================================================

    def reject_action(
        self,
        db: Session,
        action_id: int,
    ):
        action = get_agent_action_by_id(db, action_id)

        if not action:
            return {
                "success": False,
                "message": "Agent action not found.",
            }

        if action.status != "pending_approval":
            return {
                "success": False,
                "message": "Action is not waiting for approval.",
            }

        update_agent_action_status(
            db=db,
            action=action,
            status="rejected",
        )

        audit_service.log(
            db=db,
            actor="MERCHANT",
            action="REJECT_AGENT_ACTION",
            entity_type="AGENT_ACTION",
            entity_id=action.id,
            status="rejected",
            details=(
                "Merchant rejected the personalized "
                "revenue action."
            ),
        )

        db.commit()

        return {
            "success": True,
            "action_id": action.id,
            "status": "rejected",
            "message": "Revenue action rejected.",
        }


agent_action_service = AgentActionService()
