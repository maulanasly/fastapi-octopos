from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details_json: Optional[str] = None
    ip_address: Optional[str] = None
    request_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogList(BaseModel):
    total: int
    items: List[AuditLogEntry]
