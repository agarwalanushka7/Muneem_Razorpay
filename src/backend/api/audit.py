from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.services.audit_service import audit_service


router = APIRouter(
    prefix="/audit",
    tags=["Audit Trail"],
)


@router.get("/")
def get_audit_logs(
    db: Session = Depends(get_db),
):
    return audit_service.get_logs(db)


@router.get("/{log_id}")
def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
):
    log = audit_service.get_log(
        db,
        log_id,
    )

    if not log:
        raise HTTPException(
            status_code=404,
            detail="Audit log not found",
        )

    return log