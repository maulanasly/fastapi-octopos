from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SyncEventIn(BaseModel):
    client_event_id: str
    event_type: str  # order_create, order_add_payment, refund_create
    idempotency_key: str
    payload: Dict[str, Any]


class SyncBatchRequest(BaseModel):
    events: List[SyncEventIn] = Field(default_factory=list)


class SyncEventResult(BaseModel):
    client_event_id: str
    event_type: str
    status: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    message: Optional[str] = None


class SyncBatchResponse(BaseModel):
    results: List[SyncEventResult]


class SyncEventStatus(BaseModel):
    id: int
    client_event_id: str
    event_type: str
    status: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    message: Optional[str] = None
    processed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SyncEventStatusList(BaseModel):
    total: int
    items: List[SyncEventStatus]
