"""Serving queue: order-level prep state machine plus a per-tenant in-process
event hub for pushing queue changes over Server-Sent Events.

State machine (strict, forward-only)::

    queued -> preparing -> ready -> served
                 ^
                 +-- serve may skip "ready"

``serve`` may skip ``ready`` so a cashier handing over an item that needs
no preparation can complete it directly. Any other transition is rejected
with 400.

The hub is in-process: one uvicorn worker only. For multi-worker
deployments swap ``ServingHub.publish`` for Redis pub/sub (Redis is
already available in docker-compose).
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Set

# pyrefly: ignore [missing-import]
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.user import User

logger = logging.getLogger(__name__)

SERVING_QUEUED = "queued"
SERVING_PREPARING = "preparing"
SERVING_READY = "ready"
SERVING_SERVED = "served"

QUEUE_STATUSES = (SERVING_QUEUED, SERVING_PREPARING, SERVING_READY)

_ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    SERVING_QUEUED: {SERVING_PREPARING},
    SERVING_PREPARING: {SERVING_READY, SERVING_SERVED},
    SERVING_READY: {SERVING_SERVED},
}

_TIMESTAMP_COLUMNS = {
    SERVING_PREPARING: "preparing_at",
    SERVING_READY: "ready_at",
    SERVING_SERVED: "served_at",
}

_ALL_TARGETS = set().union(*_ALLOWED_TRANSITIONS.values())


class _QueueWrapper:
    """Thread-safe asyncio queue bridge: sync service code publishes to it
    while the async SSE endpoint drains it."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._queue: "asyncio.Queue[dict]" = asyncio.Queue(maxsize=100)

    def put_nowait(self, event: dict) -> None:
        if self._queue.full():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

    async def get(self, timeout: float) -> Optional[dict]:
        try:
            return await asyncio.wait_for(self._queue.get(), timeout)
        except asyncio.TimeoutError:
            return None


class ServingHub:
    """Fan-out of serving events, keyed by tenant id."""

    def __init__(self) -> None:
        self._subscribers: Dict[int, Set[_QueueWrapper]] = {}

    def subscribe(self, tenant_id: int) -> _QueueWrapper:
        wrapper = _QueueWrapper(asyncio.get_running_loop())
        self._subscribers.setdefault(tenant_id, set()).add(wrapper)
        return wrapper

    def unsubscribe(self, tenant_id: int, wrapper: _QueueWrapper) -> None:
        subscribers = self._subscribers.get(tenant_id)
        if not subscribers:
            return
        subscribers.discard(wrapper)
        if not subscribers:
            self._subscribers.pop(tenant_id, None)

    def publish(self, tenant_id: int, event: dict) -> None:
        for wrapper in list(self._subscribers.get(tenant_id, ())):
            wrapper.put_nowait(event)


serving_hub = ServingHub()


def _load_order(db: Session, order_id: int, tenant_id: int) -> Order:
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.tenant_id == tenant_id,
        )
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def transition_serving_status(
    db: Session,
    current_user: User,
    order_id: int,
    new_status: str,
    tenant_id: Optional[int] = None,
) -> Order:
    """Advance an order through the serving state machine.

    Serving is a kitchen/prep action: any staff member with ``orders:manage``
    may act on any order in the tenant's queue (unlike payments, which are
    restricted to the order's own cashier).
    """
    if tenant_id is None:
        tenant_id = current_user.tenant_id

    if new_status not in _ALL_TARGETS:
        raise HTTPException(
            status_code=400, detail=f"Invalid serving status: {new_status}"
        )

    order = _load_order(db, order_id, tenant_id)

    if order.status != "serving":
        raise HTTPException(
            status_code=400,
            detail="Only orders in serving can be advanced",
        )
    if order.serving_status not in _ALLOWED_TRANSITIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Order is not in the serving queue (status: {order.serving_status})",
        )
    if new_status not in _ALLOWED_TRANSITIONS[order.serving_status]:
        raise HTTPException(
            status_code=400,
            detail=(f"Cannot move order from {order.serving_status} to {new_status}"),
        )

    now = datetime.now(timezone.utc)
    timestamp_column = _TIMESTAMP_COLUMNS[new_status]
    if getattr(order, timestamp_column) is None:
        setattr(order, timestamp_column, now)
    order.serving_status = new_status
    if new_status == SERVING_SERVED:
        order.status = "completed"
    db.add(order)
    db.commit()
    db.refresh(order)

    serving_hub.publish(
        tenant_id,
        {"order_id": order.id, "serving_status": order.serving_status},
    )
    return order
