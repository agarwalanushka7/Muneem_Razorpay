from typing import Any


class AIPolicyService:

    def __init__(self):
        # =====================================================
        # DEFAULT MERCHANT POLICY
        # =====================================================

        self.default_policy = {
            "max_auto_action_amount": 5000.0,
            "max_discount_amount": 500.0,
            "max_discount_percentage": 5.0,
            "auto_actions_enabled": True,
            "require_approval_above_limit": True,
        }

    # =========================================================
    # GET OR CREATE POLICY
    # =========================================================

    def get_or_create_policy(
        self,
        db=None,
        merchant_id=None,
    ):
        """
        Compatibility method used by the existing
        agent_action_service.

        For the current build, MUNEEM uses a safe default
        merchant policy. This keeps the policy layer working
        without forcing changes into the action service.
        """

        return self.default_policy.copy()

    # =========================================================
    # EVALUATE ACTION
    # =========================================================

    def evaluate_action(
        self,
        policy=None,
        action_amount=None,
        action_type="",
        discount_percentage=0.0,
        discount_amount=0.0,
    ) -> dict[str, Any]:

        # -----------------------------------------------------
        # Support both calling styles:
        #
        # evaluate_action(
        #     policy,
        #     action_amount=...
        # )
        #
        # AND:
        #
        # evaluate_action(
        #     action_amount=...
        # )
        # -----------------------------------------------------

        if not isinstance(policy, dict):

            # If the first positional argument was actually
            # the action amount, move it into action_amount.
            if (
                policy is not None
                and action_amount is None
            ):
                action_amount = policy

            policy = self.default_policy.copy()

        else:
            # Make a copy so callers cannot accidentally
            # mutate the stored policy.
            policy = {
                **self.default_policy,
                **policy,
            }

        # -----------------------------------------------------
        # NORMALIZE VALUES
        # -----------------------------------------------------

        try:
            action_amount = float(
                action_amount or 0
            )
        except (TypeError, ValueError):
            return {
                "allowed": False,
                "requires_approval": False,
                "reason": "Invalid action amount.",
            }

        try:
            discount_percentage = float(
                discount_percentage or 0
            )
        except (TypeError, ValueError):
            discount_percentage = 0.0

        try:
            discount_amount = float(
                discount_amount or 0
            )
        except (TypeError, ValueError):
            discount_amount = 0.0

        action_type = (
            str(action_type or "")
            .strip()
            .lower()
            .replace(" ", "_")
        )

        # -----------------------------------------------------
        # BASIC VALIDATION
        # -----------------------------------------------------

        if action_amount < 0:
            return {
                "allowed": False,
                "requires_approval": False,
                "reason": (
                    "Action amount cannot be negative."
                ),
            }

        if discount_percentage < 0:
            return {
                "allowed": False,
                "requires_approval": False,
                "reason": (
                    "Discount percentage cannot be negative."
                ),
            }

        if discount_amount < 0:
            return {
                "allowed": False,
                "requires_approval": False,
                "reason": (
                    "Discount amount cannot be negative."
                ),
            }

        # =====================================================
        # MUNEEM IS A GROWTH AGENT
        # =====================================================

        blocked_action_types = {
            "refund",
            "issue_refund",
            "refund_customer",
            "chargeback",
        }

        if action_type in blocked_action_types:
            return {
                "allowed": False,
                "requires_approval": False,
                "reason": (
                    "Refund actions are outside "
                    "MUNEEM's revenue-growth loop."
                ),
                "policy": policy,
            }

        # =====================================================
        # POLICY SETTINGS
        # =====================================================

        max_auto_action_amount = float(
            policy.get(
                "max_auto_action_amount",
                5000.0,
            )
        )

        max_discount_amount = float(
            policy.get(
                "max_discount_amount",
                500.0,
            )
        )

        max_discount_percentage = float(
            policy.get(
                "max_discount_percentage",
                5.0,
            )
        )

        auto_actions_enabled = bool(
            policy.get(
                "auto_actions_enabled",
                True,
            )
        )

        require_approval_above_limit = bool(
            policy.get(
                "require_approval_above_limit",
                True,
            )
        )

        # =====================================================
        # AUTO ACTIONS DISABLED
        # =====================================================

        if not auto_actions_enabled:

            return {
                "allowed": True,
                "requires_approval": True,
                "reason": (
                    "Automatic actions are disabled "
                    "by merchant policy."
                ),
                "policy": policy,
            }

        # =====================================================
        # CHECK LIMITS
        # =====================================================

        reasons = []

        if (
            action_amount
            > max_auto_action_amount
        ):
            reasons.append(
                "Action amount exceeds the "
                "automatic execution limit."
            )

        if (
            discount_amount
            > max_discount_amount
        ):
            reasons.append(
                "Discount amount exceeds the "
                "automatic discount limit."
            )

        if (
            discount_percentage
            > max_discount_percentage
        ):
            reasons.append(
                "Discount percentage exceeds the "
                "automatic discount limit."
            )

        # =====================================================
        # ABOVE LIMIT
        # =====================================================

        if reasons:

            reason = " ".join(reasons)

            if require_approval_above_limit:

                return {
                    "allowed": True,
                    "requires_approval": True,
                    "reason": reason,
                    "policy": policy,
                }

            return {
                "allowed": False,
                "requires_approval": False,
                "reason": reason,
                "policy": policy,
            }

        # =====================================================
        # WITHIN LIMIT
        # =====================================================

        return {
            "allowed": True,
            "requires_approval": False,
            "reason": (
                "Action is within the merchant's "
                "automatic execution policy."
            ),
            "policy": policy,
        }


# =============================================================
# SINGLETON
# =============================================================

ai_policy_service = AIPolicyService()