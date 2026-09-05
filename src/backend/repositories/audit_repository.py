from sqlalchemy.orm import Session

from src.backend.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: int | None,
    status: str,
    details: str = "",
):
    audit_log = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        details=details,
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def get_all_audit_logs(db: Session):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .all()
    )


def get_audit_log_by_id(
    db: Session,
    log_id: int,
):
    return (
        db.query(AuditLog)
        .filter(AuditLog.id == log_id)
        .first()
    )