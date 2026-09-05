from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.services.payment_sync_service import sync_payment_statuses


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post("/sync")
def sync_payments(
    db: Session = Depends(get_db),
):
    try:
        results = sync_payment_statuses(db)

        return {
            "success": True,
            "results": results,
        }

    except Exception as exc:
        print("=" * 60)
        print("PAYMENT SYNC ERROR")
        print(type(exc).__name__)
        print(str(exc))
        print("=" * 60)

        raise HTTPException(
            status_code=500,
            detail=f"{type(exc).__name__}: {str(exc)}",
        )