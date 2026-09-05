from typing import Literal

from google import genai
from google.genai import types
from google.genai import errors

from pydantic import BaseModel, Field

from src.backend.core.config import settings


class RevenueDecision(BaseModel):

    action: Literal[
        "no_action",
        "cross_sell",
        "upsell",
        "reengage_customer",
        "create_payment",
        "offer_incentive",
    ]

    reason: str = Field(
        description=(
            "Explain why this action is likely to generate "
            "incremental revenue for the merchant."
        )
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence in the decision, from 0 to 1."
        ),
    )

    product_id: int | None = Field(
        default=None,
        description=(
            "Product to recommend when relevant."
        ),
    )

    suggested_amount: float | None = Field(
        default=None,
        ge=0.0,
        description=(
            "Amount the CUSTOMER would pay the merchant "
            "after any applicable incentive."
        ),
    )

    original_amount: float | None = Field(
        default=None,
        ge=0.0,
        description=(
            "Original product/order amount before any "
            "incentive."
        ),
    )

    discount_percentage: float | None = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description=(
            "Recommended customer discount percentage. "
            "For a strong cross-sell, upsell, or re-engagement "
            "opportunity, recommend a data-supported incentive "
            "between 1% and 10% when it can improve conversion. "
            "Use 0 only when an incentive is genuinely not "
            "needed."
        ),
    )

    expected_revenue_impact: float | None = Field(
        default=None,
        ge=0.0,
        description=(
            "Expected incremental revenue received by the merchant."
        ),
    )


class LLMService:

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    def generate_revenue_decision(
        self,
        business_context: dict,
    ) -> RevenueDecision:

        prompt = f"""
You are MUNEEM, an intelligent revenue-growth agent
working for a merchant.

Your objective is to identify a realistic opportunity
to generate INCREMENTAL REVENUE for the merchant.

The merchant should receive money from the customer.

You are NOT a refund agent.

=========================================================
BUSINESS CONTEXT
=========================================================

{business_context}


=========================================================
AVAILABLE ACTIONS
=========================================================

1. no_action

Use only when there is insufficient evidence for a
useful revenue opportunity.

2. cross_sell

Recommend a complementary product that the customer
is likely to purchase based on their previous purchases,
purchase patterns, or other available customer data.

3. upsell

Recommend a higher-value product or upgrade when the
customer behaviour supports it.

4. reengage_customer

Encourage an existing customer to make another purchase
when the available data indicates an opportunity.

5. create_payment

Create a payment request/payment link for a product or
purchase the customer is expected to make.

6. offer_incentive

Use when the primary revenue opportunity is specifically
an incentive rather than simply a product recommendation.


=========================================================
IMPORTANT BUSINESS RULES
=========================================================

1. The goal is INCREMENTAL MERCHANT REVENUE.

2. Money normally flows:

   CUSTOMER -> MERCHANT

3. Never recommend a refund as a revenue-growth action.

4. Never recommend paying money to the customer.

5. Never invent customers, products, prices, orders,
   purchase history, or behaviour.

6. Use ONLY information contained in the business context.

7. Prefer cross-sell, upsell, and re-engagement when
   the customer data supports them.

8. MUNEEM may recommend a personalized discount as part
   of a cross-sell, upsell, or re-engagement offer.

9. The merchant has final approval over the recommendation.

10. The merchant does NOT choose the discount percentage.
    MUNEEM must determine the recommended discount.

11. The recommended discount must be based on the
    available customer/business evidence.

12. Never use a discount greater than 10%.

13. When an incentive is appropriate, use the smallest
    reasonable discount supported by the customer data.

14. Do NOT automatically use 10% for every customer.

15. A discount of 0% should only be returned when the
    available evidence indicates that an incentive is
    unnecessary.

16. For a meaningful cross-sell or upsell opportunity,
    consider whether a small personalized incentive can
    increase the probability of conversion.

17. suggested_amount represents the amount the CUSTOMER
    pays.

18. original_amount represents the product price before
    the discount.

19. expected_revenue_impact represents revenue expected
    to reach the MERCHANT.

20. expected_revenue_impact must never exceed the amount
    the customer pays.

21. Do not recommend an action when there is insufficient
    evidence.

22. Do not assume automatic execution is allowed.

23. The backend policy engine independently determines
    whether the action may execute automatically.

24. Every recommendation must explain WHY it can generate
    incremental revenue.

25. For cross_sell and upsell, identify the recommended
    product using the available product information.

=========================================================
DISCOUNT DECISION
=========================================================

For cross_sell, upsell, and reengagement opportunities:

- Examine the customer's purchase frequency.
- Examine the customer's previous purchases.
- Examine available spending/value information.
- Examine whether the recommended product is relevant.
- Consider the strength of the revenue opportunity.

Use these guidelines:

Strong opportunity:
5% - 10%

Moderate opportunity:
3% - 5%

Weak but still worthwhile opportunity:
1% - 3%

No incentive needed:
0%

The exact percentage must be your decision based on
the available evidence.

Do not invent evidence.

=========================================================
OFFER CALCULATION
=========================================================

When recommending a product:

original_amount =
    original price of the recommended product

discount_percentage =
    MUNEEM's recommended discount, between 0% and 10%

suggested_amount =
    original_amount -
    discount amount

discount amount =
    original_amount *
    discount_percentage / 100

expected_revenue_impact =
    expected revenue reaching the merchant

=========================================================
IMPORTANT
=========================================================

If you choose:

cross_sell
upsell
reengage_customer
create_payment

you MAY include a discount_percentage directly in that
recommendation.

The discount does NOT require the action type to be
"offer_incentive".

The product recommendation and personalized incentive
are part of the same MUNEEM revenue action.

Return a structured decision.
"""

        # =====================================================
        # GEMINI REQUEST
        # =====================================================

        try:

            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RevenueDecision,
                ),
            )

        except errors.ClientError as exc:

            error_message = str(exc)

            if (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            ):

                raise RuntimeError(
                    "Gemini API quota has been exhausted. "
                    "Please wait for the quota to reset or "
                    "check your Gemini API billing/quota settings."
                ) from exc

            raise RuntimeError(
                f"Gemini API request failed: {error_message}"
            ) from exc

        except Exception as exc:

            raise RuntimeError(
                f"Unexpected error while calling Gemini: {str(exc)}"
            ) from exc

        # =====================================================
        # EMPTY RESPONSE
        # =====================================================

        if not response.text:

            raise ValueError(
                "Gemini returned an empty response."
            )

        # =====================================================
        # PARSE RESPONSE
        # =====================================================

        try:

            decision = RevenueDecision.model_validate_json(
                response.text
            )

        except Exception as exc:

            raise ValueError(
                "Gemini returned an invalid revenue decision."
            ) from exc

        # =====================================================
        # NORMALIZE DISCOUNT
        # =====================================================

        discount = float(
            decision.discount_percentage
            if decision.discount_percentage is not None
            else 0.0
        )

        # Never allow more than 10%.
        discount = min(
            10.0,
            max(
                0.0,
                discount,
            ),
        )

        decision.discount_percentage = discount

        # =====================================================
        # OFFER VALIDATION
        # =====================================================

        if decision.discount_percentage > 0:

            if (
                decision.original_amount is None
                and decision.suggested_amount is None
            ):

                raise ValueError(
                    "A discounted recommendation requires "
                    "an original or suggested amount."
                )

        # =====================================================
        # CALCULATE OFFER WHEN ORIGINAL PRICE EXISTS
        # =====================================================

        if decision.original_amount is not None:

            original_amount = float(
                decision.original_amount
            )

            discount_amount = round(
                original_amount
                * decision.discount_percentage
                / 100,
                2,
            )

            calculated_amount = round(
                original_amount
                - discount_amount,
                2,
            )

            # -------------------------------------------------
            # MUNEEM's calculated customer payable amount
            # becomes the source of truth.
            # -------------------------------------------------

            decision.suggested_amount = (
                calculated_amount
            )

        # =====================================================
        # VALIDATE CUSTOMER PAYABLE AMOUNT
        # =====================================================

        if (
            decision.original_amount is not None
            and decision.suggested_amount is not None
        ):

            if (
                decision.suggested_amount
                > decision.original_amount
            ):

                raise ValueError(
                    "Customer payable amount cannot exceed "
                    "the original amount."
                )

            if decision.suggested_amount < 0:

                raise ValueError(
                    "Customer payable amount cannot be negative."
                )

        # =====================================================
        # EXPECTED REVENUE VALIDATION
        # =====================================================

        if (
            decision.expected_revenue_impact is not None
            and decision.suggested_amount is not None
        ):

            if (
                decision.expected_revenue_impact
                > decision.suggested_amount
            ):

                raise ValueError(
                    "Expected merchant revenue cannot exceed "
                    "the customer payable amount."
                )

        # =====================================================
        # ACTION-SPECIFIC VALIDATION
        # =====================================================

        if decision.action in {
            "cross_sell",
            "upsell",
            "create_payment",
            "reengage_customer",
        }:

            if decision.suggested_amount is not None:

                if decision.suggested_amount < 0:

                    raise ValueError(
                        "Customer payable amount cannot be negative."
                    )

            if decision.expected_revenue_impact is not None:

                if decision.expected_revenue_impact < 0:

                    raise ValueError(
                        "Expected revenue cannot be negative."
                    )

        # =====================================================
        # FINAL SAFETY
        # =====================================================

        if decision.discount_percentage > 10:

            decision.discount_percentage = 10.0

        return decision


llm_service = LLMService()