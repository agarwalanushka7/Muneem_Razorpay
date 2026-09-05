from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.agents.revenue_agent import revenue_agent


router = APIRouter(
    prefix="/agent",
    tags=["AI Revenue Agent"],
)


@router.post(
    "/analyze/{opportunity_id}"
)
def analyze_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
):
    result = revenue_agent.analyze_opportunity(
        db,
        opportunity_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["message"],
        )

    return result