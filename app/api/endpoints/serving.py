import asyncio
import json

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_current_active_user_any_auth, require_permissions
from app.core.database import get_db
from app.models.order import Order
from app.models.user import User
from app.schemas.order import Order as OrderSchema
from app.services.serving import (
    QUEUE_STATUSES,
    SERVING_PREPARING,
    SERVING_READY,
    SERVING_SERVED,
    serving_hub,
    transition_serving_status,
)

router = APIRouter()

_KEEPALIVE_SECONDS = 15.0


@router.get("/", response_model=list[OrderSchema])
def get_serving_queue(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: str | None = Query(
        None, description="Filter by serving status: queued, preparing, ready"
    ),
    response: Response = None,
    current_user: User = Depends(require_permissions("orders:manage")),
):
    query = (
        db.query(Order)
        .filter(
            Order.tenant_id == current_user.tenant_id,
            Order.status == "serving",
            Order.serving_status.in_(QUEUE_STATUSES),
        )
        .options(joinedload(Order.items), joinedload(Order.customer))
        .order_by(Order.created_at.asc())
    )
    if status:
        query = query.filter(Order.serving_status == status)

    limit = min(limit, 200)
    total = query.count()
    orders = query.offset(skip).limit(limit).all()
    response.headers["X-Total-Count"] = str(total)
    return orders


@router.post("/{order_id}/start", response_model=OrderSchema)
def start_serving(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders:manage")),
):
    return transition_serving_status(db, current_user, order_id, SERVING_PREPARING)


@router.post("/{order_id}/ready", response_model=OrderSchema)
def mark_ready(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders:manage")),
):
    return transition_serving_status(db, current_user, order_id, SERVING_READY)


@router.post("/{order_id}/serve", response_model=OrderSchema)
def mark_served(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders:manage")),
):
    return transition_serving_status(db, current_user, order_id, SERVING_SERVED)


@router.get("/stream")
async def stream_serving_events(
    current_user: User = Depends(get_current_active_user_any_auth),
):
    """Server-Sent Events feed for the tenant.

    Auth accepts the ``Authorization`` header (for HTTP clients) or a
    ``?token=<jwt>`` query parameter (EventSource-style clients cannot set
    headers). Two event kinds on one stream:

    * ``serving``: ``{"order_id": int, "serving_status": str}``
    * ``tracking``: ``{"order_id": int, "tracking_status": str, ...}``
    """

    tenant_id = current_user.tenant_id

    async def event_stream():
        wrapper = serving_hub.subscribe(tenant_id)
        try:
            yield ": connected\n\n"
            while True:
                event = await wrapper.get(_KEEPALIVE_SECONDS)
                if event is None:
                    yield ": ping\n\n"
                    continue
                event_name = "tracking" if "tracking_status" in event else "serving"
                yield f"event: {event_name}\ndata: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            raise
        finally:
            serving_hub.unsubscribe(tenant_id, wrapper)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
