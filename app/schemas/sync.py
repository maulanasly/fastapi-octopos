from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SyncEventIn(BaseModel):
    client_event_id: str
    event_type: str  # order_create, order_add_payment, refund_create
    idempotency_key: str
    payload: dict[str, Any]


class SyncBatchRequest(BaseModel):
    events: list[SyncEventIn] = Field(default_factory=list)


class SyncEventResult(BaseModel):
    client_event_id: str
    event_type: str
    status: str
    resource_type: str | None = None
    resource_id: int | None = None
    message: str | None = None


class SyncBatchResponse(BaseModel):
    results: list[SyncEventResult]


class SyncEventStatus(BaseModel):
    id: int
    client_event_id: str
    event_type: str
    status: str
    resource_type: str | None = None
    resource_id: int | None = None
    message: str | None = None
    processed_at: datetime | None = None

    model_config = {"from_attributes": True}


class SyncEventStatusList(BaseModel):
    total: int
    items: list[SyncEventStatus]
