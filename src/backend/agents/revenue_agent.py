from typing import Any

from sqlalchemy.orm import Session

from src.backend.models.customer import Customer
from src.backend.models.opportunity import Opportunity
from src.backend.models.product import Product

from src.backend.services.cross_sell_service import (
    find_cross_sell_customers,
)

from src.backend.services.llm_service import (
    llm_service,
)

from src.backend.services.ai_policy_service import (
    ai_policy_service,
)


def _customer_discount(
    total_orders,
    total_spent,
):
    """
    MUNEEM's customer-specific discount recommendation.

    The recommendation is based on actual customer behaviour.

    0-1 orders  -> 5%
    2-3 orders  -> 7%
    4+ orders   -> 10%

    High-value customers can receive the stronger
    applicable discount.

    Maximum is always 10%.
    """

    try:
        orders = int(total_orders or 0)
    except (TypeError, ValueError):
        orders = 0

    try:
        spent = float(total_spent or 0)
    except (TypeError, ValueError):
        spent = 0.0

    if orders >= 4:
        discount = 10.0
    elif orders >= 2:
        discount = 7.0
    else:
        discount = 5.0

    if spent >= 10000:
        discount = 10.0
    elif spent >= 5000:
        discount = max(discount, 7.0)

    return min(10.0, max(0.0, discount))


class RevenueAgent:

    # =========================================================
    # ANALYZE OPPORTUNITY
    # =========================================================

    def analyze_opportunity(
        self,
        db: Session,
        opportunity_id: int,
    ) -> dict[str, Any]:

        opportunity = (
            db.query(Opportunity)
            .filter(
                Opportunity.id == opportunity_id
            )
            .first()
        )

        if not opportunity:
            return {
                "success": False,
                "message": "Opportunity not found.",
            }

        # =====================================================
        # SOURCE PRODUCT
        # =====================================================

        source_product = None

        if opportunity.product_id:
            source_product = (
                db.query(Product)
                .filter(
                    Product.id
                    == opportunity.product_id
                )
                .first()
            )

        # =====================================================
        # RECOMMENDED PRODUCT
        # =====================================================

        recommended_product = None

        if opportunity.related_product_id:
            recommended_product = (
                db.query(Product)
                .filter(
                    Product.id
                    == opportunity.related_product_id
                )
                .first()
            )

        # =====================================================
        # CROSS-SELL INVESTIGATION
        # =====================================================

        agent_investigation = {
            "cross_sell_customers": {
                "customer_ids": [],
                "count": 0,
            }
        }

        selected_customer = None

        if (
            opportunity.opportunity_type
            == "cross_sell"
            and opportunity.product_id
            and opportunity.related_product_id
        ):

            cross_sell_result = (
                find_cross_sell_customers(
                    db=db,
                    product_id=opportunity.product_id,
                    related_product_id=(
                        opportunity.related_product_id
                    ),
                )
            )

            agent_investigation[
                "cross_sell_customers"
            ] = cross_sell_result

            customer_ids = (
                cross_sell_result.get(
                    "customer_ids",
                    [],
                )
            )

            if customer_ids:
                selected_customer = (
                    db.query(Customer)
                    .filter(
                        Customer.id
                        == customer_ids[0]
                    )
                    .first()
                )

        # =====================================================
        # FALLBACK CUSTOMER
        # =====================================================

        if not selected_customer:

            customer_id = getattr(
                opportunity,
                "customer_id",
                None,
            )

            if customer_id:
                selected_customer = (
                    db.query(Customer)
                    .filter(
                        Customer.id
                        == customer_id
                    )
                    .first()
                )

        # =====================================================
        # BUSINESS CONTEXT
        # =====================================================

        business_context = {
            "opportunity": {
                "id": opportunity.id,
                "type": opportunity.opportunity_type,
                "title": opportunity.title,
                "description": opportunity.description,
                "estimated_value": opportunity.estimated_value,
                "confidence": opportunity.confidence,
            },

            "source_product": (
                {
                    "id": source_product.id,
                    "name": source_product.name,
                    "price": source_product.price,
                    "inventory": source_product.inventory,
                }
                if source_product
                else None
            ),

            "recommended_product": (
                {
                    "id": recommended_product.id,
                    "name": recommended_product.name,
                    "price": recommended_product.price,
                    "inventory": recommended_product.inventory,
                }
                if recommended_product
                else None
            ),

            "customer": (
                {
                    "id": selected_customer.id,
                    "name": selected_customer.name,
                    "email": selected_customer.email,
                    "total_orders": (
                        selected_customer.total_orders
                    ),
                    "total_spent": (
                        selected_customer.total_spent
                    ),
                }
                if selected_customer
                else None
            ),

            "agent_investigation": agent_investigation,
        }

        # =====================================================
        # ASK LLM
        # =====================================================

        try:

            ai_decision = (
                llm_service.generate_revenue_decision(
                    business_context=business_context
                )
            )

        except Exception as exc:

            print(
                "REVENUE AI ERROR:",
                repr(exc),
            )

            return {
                "success": False,
                "message": (
                    "MUNEEM could not generate "
                    "a revenue decision."
                ),
                "error": repr(exc),
            }

        # =====================================================
        # CONVERT MODEL TO DICT
        # =====================================================

        if hasattr(ai_decision, "model_dump"):

            decision_data = ai_decision.model_dump()

        elif hasattr(ai_decision, "dict"):

            decision_data = ai_decision.dict()

        elif isinstance(ai_decision, dict):

            decision_data = ai_decision

        else:

            return {
                "success": False,
                "message": (
                    "MUNEEM received an invalid "
                    "AI decision."
                ),
            }

        # =====================================================
        # ACTION TYPE
        # =====================================================

        action_type = (
            decision_data.get("action_type")
            or decision_data.get("action")
            or ""
        )

        action_type = (
            str(action_type)
            .strip()
            .lower()
            .replace(" ", "_")
        )

        if opportunity.opportunity_type == "cross_sell":
            action_type = "cross_sell"

        # =====================================================
        # NO ACTION
        # =====================================================

        if action_type in {
            "",
            "none",
            "no_action",
            "do_nothing",
        }:

            return {
                "success": True,
                "message": (
                    "MUNEEM decided that "
                    "no action is required."
                ),
                "opportunity": {
                    "id": opportunity.id,
                    "opportunity_type": (
                        opportunity.opportunity_type
                    ),
                    "title": opportunity.title,
                    "description": opportunity.description,
                },
                "agent_investigation": agent_investigation,
                "ai_decision": decision_data,
                "execution_status": "no_action",
            }

        # =====================================================
        # CUSTOMER
        # =====================================================

        ai_customer_id = decision_data.get(
            "customer_id"
        )

        if (
            ai_customer_id
            and not selected_customer
        ):

            selected_customer = (
                db.query(Customer)
                .filter(
                    Customer.id
                    == ai_customer_id
                )
                .first()
            )

        if selected_customer:
            ai_customer_id = selected_customer.id

        # =====================================================
        # PRODUCT
        # =====================================================

        ai_product_id = decision_data.get(
            "product_id"
        )

        if (
            opportunity.opportunity_type
            == "cross_sell"
            and opportunity.related_product_id
        ):

            ai_product_id = (
                opportunity.related_product_id
            )

        if (
            not ai_product_id
            and recommended_product
        ):

            ai_product_id = recommended_product.id

        if ai_product_id:

            final_product = (
                db.query(Product)
                .filter(
                    Product.id
                    == ai_product_id
                )
                .first()
            )

            if final_product:
                recommended_product = final_product

        # =====================================================
        # PRICE
        # =====================================================

        original_amount = 0.0

        if recommended_product:

            try:
                original_amount = float(
                    recommended_product.price or 0
                )
            except (TypeError, ValueError):
                original_amount = 0.0

        if original_amount <= 0:

            return {
                "success": False,
                "message": (
                    "MUNEEM could not create the "
                    "offer because the product price "
                    "is invalid."
                ),
            }

        # =====================================================
        # AI DISCOUNT
        # =====================================================

        ai_discount = decision_data.get(
            "discount_percentage"
        )

        try:

            discount_percentage = float(
                ai_discount
                if ai_discount is not None
                else 0
            )

        except (
            TypeError,
            ValueError,
        ):

            discount_percentage = 0.0

        # =====================================================
        # IMPORTANT:
        # IF AI RETURNS 0, USE CUSTOMER DATA.
        #
        # This prevents a valid customer offer from
        # becoming 0% simply because the LLM omitted
        # the optional discount field.
        # =====================================================

        if (
            discount_percentage <= 0
            and selected_customer
        ):

            discount_percentage = (
                _customer_discount(
                    selected_customer.total_orders,
                    selected_customer.total_spent,
                )
            )

        # =====================================================
        # HARD SAFETY LIMIT
        # =====================================================

        discount_percentage = min(
            10.0,
            max(
                0.0,
                discount_percentage,
            ),
        )

        # =====================================================
        # OFFER CALCULATION
        # =====================================================

        discount_amount = round(
            original_amount
            * discount_percentage
            / 100,
            2,
        )

        final_amount = round(
            original_amount
            - discount_amount,
            2,
        )

        # =====================================================
        # MERCHANT POLICY
        # =====================================================

        merchant_policy = (
            ai_policy_service.get_or_create_policy(
                db=db
            )
        )

        policy_result = (
            ai_policy_service.evaluate_action(
                policy=merchant_policy,
                action_amount=final_amount,
                action_type=action_type,
                discount_percentage=(
                    discount_percentage
                ),
                discount_amount=discount_amount,
            )
        )

        allowed = bool(
            policy_result.get(
                "allowed",
                False,
            )
        )

        requires_approval = bool(
            policy_result.get(
                "requires_approval",
                True,
            )
        )

        if not allowed:
            execution_status = "blocked"

        elif requires_approval:
            execution_status = "pending_approval"

        else:
            execution_status = "auto_execute"

        # =====================================================
        # FINAL RESPONSE
        # =====================================================

        return {
            "success": True,

            "message": (
                "MUNEEM prepared a personalized "
                f"{recommended_product.name} offer "
                f"for "
                f"{selected_customer.name if selected_customer else 'the customer'}."
            ),

            "opportunity": {
                "id": opportunity.id,
                "opportunity_type": (
                    opportunity.opportunity_type
                ),
                "title": opportunity.title,
                "description": opportunity.description,
                "estimated_value": opportunity.estimated_value,
                "confidence": opportunity.confidence,
            },

            "agent_investigation": agent_investigation,

            "ai_decision": decision_data,

            "customer": (
                {
                    "id": selected_customer.id,
                    "name": selected_customer.name,
                    "email": selected_customer.email,
                    "total_orders": (
                        selected_customer.total_orders
                    ),
                    "total_spent": (
                        selected_customer.total_spent
                    ),
                }
                if selected_customer
                else None
            ),

            "product": {
                "id": recommended_product.id,
                "name": recommended_product.name,
                "price": recommended_product.price,
                "inventory": recommended_product.inventory,
            },

            "offer": {
                "original_amount": original_amount,
                "discount_percentage": (
                    discount_percentage
                ),
                "discount_amount": discount_amount,
                "final_amount": final_amount,
                "expected_revenue": final_amount,
            },

            "policy": policy_result,

            "execution_status": execution_status,

            "action_type": action_type,

            "customer_id": (
                selected_customer.id
                if selected_customer
                else ai_customer_id
            ),

            "product_id": ai_product_id,

            "original_amount": original_amount,

            "discount_percentage": (
                discount_percentage
            ),

            "discount_amount": discount_amount,

            "final_amount": final_amount,
        }


revenue_agent = RevenueAgent()