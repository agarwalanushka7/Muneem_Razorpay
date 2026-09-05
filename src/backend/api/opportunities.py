from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.models.opportunity import Opportunity
from src.backend.services.opportunity_service import (
    detect_cross_sell_opportunities,
)


router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities"],
)


@router.get("/")
def get_opportunities(
    db: Session = Depends(get_db),
):
    return (
        db.query(Opportunity)
        .order_by(Opportunity.id.desc())
        .all()
    )


@router.post("/detect")
def detect_opportunities(
    db: Session = Depends(get_db),
):
    opportunities = detect_cross_sell_opportunities(db)

    return {
        "message": "Opportunity detection completed",
        "count": len(opportunities),
        "opportunities": opportunities,
    }