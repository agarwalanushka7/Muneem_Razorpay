from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
)

from src.backend.database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
        unique=True,
    )

    display_name = Column(
        String,
        nullable=False,
    )

    platform_type = Column(
        String,
        nullable=False,
        default="sales_channel",
    )

    connection_type = Column(
        String,
        nullable=False,
        default="manual",
    )

    status = Column(
        String,
        nullable=False,
        default="disconnected",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    last_synced_at = Column(
        DateTime,
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