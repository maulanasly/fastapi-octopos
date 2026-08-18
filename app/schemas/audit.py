from datetime import datetime

from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    id: int
    user_id: int | None = None
    action: str
    resource_type: str | None = None
    resource_id: int | None = None
    details_json: str | None = None
    ip_address: str | None = None
    request_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogList(BaseModel):
    total: int
    items: list[AuditLogEntry]
