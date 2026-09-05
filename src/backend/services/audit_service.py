from sqlalchemy.orm import Session

from src.backend.repositories.audit_repository import (
    create_audit_log,
    get_all_audit_logs,
    get_audit_log_by_id,
)


class AuditService:

    def log(
        self,
        db: Session,
        actor: str,
        action: str,
        entity_type: str,
        entity_id: int | None,
        status: str,
        details: str = "",
    ):
        return create_audit_log(
            db=db,
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            details=details,
        )

    def get_logs(self, db: Session):
        return get_all_audit_logs(db)

    def get_log(
        self,
        db: Session,
        log_id: int,
    ):
        return get_audit_log_by_id(
            db,
            log_id,
        )


audit_service = AuditService()