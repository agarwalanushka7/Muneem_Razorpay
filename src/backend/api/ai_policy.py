from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.schemas.ai_policy import (
    AIPolicyResponse,
    AIPolicyUpdate,
)
from src.backend.services.ai_policy_service import (
    ai_policy_service,
)


router = APIRouter(
    prefix="/ai-policy",
    tags=["AI Policy"],
)


@router.get(
    "/",
    response_model=AIPolicyResponse,
)
def get_ai_policy(
    db: Session = Depends(get_db),
):
    return ai_policy_service.get_or_create_policy(db)


@router.put(
    "/",
    response_model=AIPolicyResponse,
)
def update_ai_policy(
    policy_data: AIPolicyUpdate,
    db: Session = Depends(get_db),
):
    return ai_policy_service.update_policy(
        db=db,
        max_auto_action_amount=(
            policy_data.max_auto_action_amount
        ),
        max_discount_amount=(
            policy_data.max_discount_amount
        ),
        max_discount_percentage=(
            policy_data.max_discount_percentage
        ),
        auto_actions_enabled=(
            policy_data.auto_actions_enabled
        ),
        require_approval_above_limit=(
            policy_data.require_approval_above_limit
        ),
    )