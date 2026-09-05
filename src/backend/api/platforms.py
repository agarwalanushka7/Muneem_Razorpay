from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.models.platform import Platform

from src.backend.repositories.platform_repository import (
    create_platform,
    get_all_platforms,
    get_platform_by_id,
    update_platform_status,
)

from src.backend.schemas.platform import (
    PlatformCreate,
    PlatformResponse,
)

from src.backend.services.platform_sync_service import (
    platform_sync_service,
)


router = APIRouter(
    prefix="/platforms",
    tags=["Platforms"],
)


# =========================================================
# AVAILABLE SALES CHANNELS
# =========================================================

AVAILABLE_CHANNELS = [
    {
        "name": "direct",
        "display_name": "Direct Store",
        "platform_type": "sales_channel",
        "connection_type": "native",
        "description": "Connect your own store data.",
        "import_types": ["xlsx", "xls", "csv"],
    },
    {
        "name": "blinkit",
        "display_name": "Blinkit",
        "platform_type": "sales_channel",
        "connection_type": "manual",
        "description": "Import your Blinkit sales export.",
        "import_types": ["xlsx", "xls", "csv", "pdf"],
    },
    {
        "name": "zepto",
        "display_name": "Zepto",
        "platform_type": "sales_channel",
        "connection_type": "manual",
        "description": "Import your Zepto sales export.",
        "import_types": ["xlsx", "xls", "csv", "pdf"],
    },
]


@router.get("/available")
def get_available_channels():
    """
    Returns the sales channels that MUNEEM currently supports.

    These are application-level channel definitions.
    No merchant/customer/order/product data is hardcoded here.
    """
    return AVAILABLE_CHANNELS


# =========================================================
# SYNC REQUEST
# =========================================================


class PlatformSyncRequest(BaseModel):
    products: list[dict[str, Any]] = Field(default_factory=list)
    customers: list[dict[str, Any]] = Field(default_factory=list)
    orders: list[dict[str, Any]] = Field(default_factory=list)
    transactions: list[dict[str, Any]] = Field(default_factory=list)


# =========================================================
# GET ALL CONNECTED PLATFORMS
# =========================================================


@router.get(
    "",
    response_model=list[PlatformResponse],
)
def list_platforms(
    db: Session = Depends(get_db),
):
    return get_all_platforms(db)


# =========================================================
# CREATE PLATFORM
# =========================================================


@router.post(
    "",
    response_model=PlatformResponse,
)
def add_platform(
    platform_data: PlatformCreate,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Platform)
        .filter(
            Platform.name == platform_data.name
        )
        .first()
    )

    if existing:
        # If the platform already exists but was disconnected,
        # simply reconnect it instead of creating a duplicate.
        if not existing.is_active:
            return update_platform_status(
                db=db,
                platform=existing,
                status="connected",
                is_active=True,
            )

        raise HTTPException(
            status_code=400,
            detail="Platform is already connected.",
        )

    return create_platform(
        db=db,
        name=platform_data.name,
        display_name=platform_data.display_name,
        platform_type=platform_data.platform_type,
        connection_type=platform_data.connection_type,
    )


# =========================================================
# CONNECT PLATFORM
# =========================================================


@router.post(
    "/{platform_id}/connect",
    response_model=PlatformResponse,
)
def connect_platform(
    platform_id: int,
    db: Session = Depends(get_db),
):
    platform = get_platform_by_id(
        db,
        platform_id,
    )

    if platform is None:
        raise HTTPException(
            status_code=404,
            detail="Platform not found.",
        )

    return update_platform_status(
        db=db,
        platform=platform,
        status="connected",
        is_active=True,
    )


# =========================================================
# DISCONNECT PLATFORM
# =========================================================


@router.post(
    "/{platform_id}/disconnect",
    response_model=PlatformResponse,
)
def disconnect_platform(
    platform_id: int,
    db: Session = Depends(get_db),
):
    platform = get_platform_by_id(
        db,
        platform_id,
    )

    if platform is None:
        raise HTTPException(
            status_code=404,
            detail="Platform not found.",
        )

    return update_platform_status(
        db=db,
        platform=platform,
        status="disconnected",
        is_active=False,
    )


# =========================================================
# SYNC PLATFORM DATA
# =========================================================


@router.post(
    "/{platform_id}/sync",
)
def sync_platform(
    platform_id: int,
    sync_data: PlatformSyncRequest,
    db: Session = Depends(get_db),
):
    platform = get_platform_by_id(
        db,
        platform_id,
    )

    if platform is None:
        raise HTTPException(
            status_code=404,
            detail="Platform not found.",
        )

    if not platform.is_active:
        raise HTTPException(
            status_code=400,
            detail="Connect this platform before importing data.",
        )

    return platform_sync_service.sync_platform_data(
        db=db,
        platform_id=platform_id,
        data=sync_data.model_dump(),
    )