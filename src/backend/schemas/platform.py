from datetime import datetime

from pydantic import BaseModel


class PlatformResponse(BaseModel):
    id: int
    name: str
    display_name: str
    platform_type: str
    connection_type: str
    status: str
    is_active: bool
    last_synced_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class PlatformCreate(BaseModel):
    name: str
    display_name: str
    platform_type: str = "sales_channel"
    connection_type: str = "manual"