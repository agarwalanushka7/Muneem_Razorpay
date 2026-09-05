from sqlalchemy.orm import Session

from src.backend.models.agent_action import AgentAction


def create_agent_action(
    db: Session,
    opportunity_id: int,
    action_type: str,
    action_amount: float,
    approval_required: int,
    status: str,
    customer_id: int | None = None,
    product_id: int | None = None,
    original_amount: float | None = None,
    discount_percentage: float = 0.0,
    discount_amount: float = 0.0,
    final_amount: float | None = None,
    customer_message: str | None = None,
):
    """
    Create and persist a MUNEEM agent action.

    action_amount represents the final amount
    the customer will pay.
    """

    action = AgentAction(
        opportunity_id=opportunity_id,
        customer_id=customer_id,
        product_id=product_id,
        action_type=action_type,
        action_amount=action_amount,
        original_amount=original_amount,
        discount_percentage=discount_percentage,
        discount_amount=discount_amount,
        final_amount=final_amount,
        customer_message=customer_message,
        approval_required=approval_required,
        status=status,
    )

    db.add(action)
    db.commit()
    db.refresh(action)

    return action


def get_agent_action_by_id(
    db: Session,
    action_id: int,
):
    """
    Get a single agent action by its internal ID.
    """

    return (
        db.query(AgentAction)
        .filter(
            AgentAction.id == action_id
        )
        .first()
    )


def get_agent_action_by_opportunity_and_customer(
    db: Session,
    opportunity_id: int,
    customer_id: int,
):
    """
    Prevent duplicate active actions for the
    same opportunity and customer.

    Example:

    Sports Socks → Running Shoes
    +
    Aarav

    should produce only one active action.
    """

    return (
        db.query(AgentAction)
        .filter(
            AgentAction.opportunity_id
            == opportunity_id,
            AgentAction.customer_id
            == customer_id,
            AgentAction.status.notin_(
                ["rejected"]
            ),
        )
        .order_by(
            AgentAction.id.desc()
        )
        .first()
    )


def get_all_agent_actions(
    db: Session,
):
    """
    Return all agent actions, newest first.
    """

    return (
        db.query(AgentAction)
        .order_by(
            AgentAction.id.desc()
        )
        .all()
    )


def update_agent_action_status(
    db: Session,
    action: AgentAction,
    status: str,
    execution_result: str | None = None,
):
    """
    Update the lifecycle state of an agent action.

    Typical lifecycle:

    pending_approval
        ↓
    approved
        ↓
    executed

    Or:

    pending_approval
        ↓
    rejected

    Or:

    approved
        ↓
    failed
    """

    action.status = status

    if execution_result is not None:
        action.execution_result = execution_result

    db.commit()
    db.refresh(action)

    return action