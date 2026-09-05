from datetime import datetime

from sqlalchemy.orm import Session

from src.backend.models.platform import Platform


def get_all_platforms(
    db: Session,
):
    return (
        db.query(Platform)
        .order_by(Platform.id.asc())
        .all()
    )


def get_platform_by_id(
    db: Session,
    platform_id: int,
):
    return (
        db.query(Platform)
        .filter(
            Platform.id == platform_id
        )
        .first()
    )


def get_platform_by_name(
    db: Session,
    name: str,
):
    return (
        db.query(Platform)
        .filter(
            Platform.name == name
        )
        .first()
    )


def create_platform(
    db: Session,
    name: str,
    display_name: str,
    platform_type: str = "sales_channel",
    connection_type: str = "manual",
):
    platform = Platform(
        name=name,
        display_name=display_name,
        platform_type=platform_type,
        connection_type=connection_type,
        status="disconnected",
        is_active=False,
    )

    db.add(platform)
    db.commit()
    db.refresh(platform)

    return platform


def update_platform_status(
    db: Session,
    platform: Platform,
    status: str,
    is_active: bool,
):
    platform.status = status
    platform.is_active = is_active

    if status == "connected":
        platform.last_synced_at = datetime.utcnow()

    db.commit()
    db.refresh(platform)

    return platform