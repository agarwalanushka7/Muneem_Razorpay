from sqlalchemy.orm import Session

from src.backend.models.ai_policy import AIPolicy


def get_policy(db: Session):
    return (
        db.query(AIPolicy)
        .order_by(AIPolicy.id.asc())
        .first()
    )


def create_default_policy(db: Session):
    policy = AIPolicy()

    db.add(policy)
    db.commit()
    db.refresh(policy)

    return policy


def update_policy(
    db: Session,
    policy: AIPolicy,
    max_auto_action_amount: float,
    max_discount_amount: float,
    max_discount_percentage: float,
    auto_actions_enabled: bool,
    require_approval_above_limit: bool,
):
    policy.max_auto_action_amount = max_auto_action_amount
    policy.max_discount_amount = max_discount_amount
    policy.max_discount_percentage = max_discount_percentage
    policy.auto_actions_enabled = auto_actions_enabled
    policy.require_approval_above_limit = (
        require_approval_above_limit
    )

    db.commit()
    db.refresh(policy)

    return policy