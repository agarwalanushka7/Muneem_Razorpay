from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from src.backend.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    actor = Column(
        String,
        nullable=False,
    )

    action = Column(
        String,
        nullable=False,
    )

    entity_type = Column(
        String,
        nullable=False,
    )

    entity_id = Column(
        Integer,
        nullable=True,
    )

    status = Column(
        String,
        nullable=False,
    )

    details = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )