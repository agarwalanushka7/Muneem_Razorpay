from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from src.backend.database import Base


class AgentAction(Base):

    __tablename__ = "agent_actions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    opportunity_id = Column(
        Integer,
        ForeignKey("opportunities.id"),
        nullable=False,
    )

    # Customer this action is intended for.
    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=True,
    )

    # Product being recommended.
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=True,
    )

    action_type = Column(
        String,
        nullable=False,
    )

    # Final amount customer will pay.
    action_amount = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    # Offer pricing.
    original_amount = Column(
        Float,
        nullable=True,
    )

    discount_percentage = Column(
        Float,
        nullable=True,
        default=0.0,
    )

    discount_amount = Column(
        Float,
        nullable=True,
        default=0.0,
    )

    final_amount = Column(
        Float,
        nullable=True,
    )

    # Customer-facing message.
    customer_message = Column(
        Text,
        nullable=True,
    )

    approval_required = Column(
        Integer,
        nullable=False,
        default=0,
    )

    status = Column(
        String,
        nullable=False,
        default="pending",
    )

    execution_result = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )