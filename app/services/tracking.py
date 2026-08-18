"""Order tracking: destination-aware service trips plus location pings.

State machine (strict, forward-only)::

    none -> assigned -> en_route -> on_site

Tracked orders are paid orders (``status == "serving"``) that carry a
destination — e.g. a mobile car wash driving to the customer's car. The
serving machine then handles the on-site work (preparing/ready/served).

Location pings are appended to ``order_location_updates`` (history +
latest position) and fanned out to the same per-tenant in-process SSE
hub the serving queue uses (``event: tracking``). For multi-worker
deployments swap the hub for Redis pub/sub (Redis is already available
in docker-compose).
"""

from datetime import UTC, datetime

# pyrefly: ignore [missing-import]
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.order import Order, OrderLocationUpdate
from app.models.user import User
from app.services.serving import serving_hub

TRACKING_NONE = "none"
TRACKING_ASSIGNED = "assigned"
TRACKING_EN_ROUTE = "en_route"
TRACKING_ON_SITE = "on_site"

TRACKING_TARGETS = (TRACKING_ASSIGNED, TRACKING_EN_ROUTE, TRACKING_ON_SITE)

_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    TRACKING_ASSIGNED: {TRACKING_EN_ROUTE},
    TRACKING_EN_ROUTE: {TRACKING_ON_SITE},
}

_TIMESTAMP_COLUMNS = {
    TRACKING_ASSIGNED: "assigned_at",
    TRACKING_EN_ROUTE: "en_route_at",
    TRACKING_ON_SITE: "on_site_at",
}


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


def _publish(
    tenant_id: int,
    order: Order,
    lat: float | None = None,
    lng: float | None = None,
) -> None:
    event = {
        "order_id": order.id,
        "tracking_status": order.tracking_status,
    }
    if lat is not None and lng is not None:
        event.update({"lat": lat, "lng": lng})
    serving_hub.publish(tenant_id, event)


def transition_tracking_status(
    db: Session,
    current_user: User,
    order_id: int,
    new_status: str,
    tenant_id: int | None = None,
) -> Order:
    """Advance an order through the tracking state machine.

    Requires ``orders:track`` (enforced by the endpoint). Only paid orders
    (``status == "serving"``) that are tracked (``tracking_status != none``
    or entering ``assigned`` with a destination) can be advanced.
    """
    if tenant_id is None:
        tenant_id = current_user.tenant_id

    if new_status not in TRACKING_TARGETS:
        raise HTTPException(
            status_code=400, detail=f"Invalid tracking status: {new_status}"
        )

    order = _load_order(db, order_id, tenant_id)

    if order.status != "serving":
        raise HTTPException(
            status_code=400,
            detail="Only paid orders can be tracked",
        )
    if order.tracking_status == TRACKING_NONE:
        if new_status != TRACKING_ASSIGNED:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Order is not being tracked (status: {order.tracking_status})"
                ),
            )
        if order.destination is None:
            raise HTTPException(
                status_code=400,
                detail="Order has no destination; set one before assigning",
            )
    elif order.tracking_status not in _ALLOWED_TRANSITIONS:
        raise HTTPException(
            status_code=400,
            detail=(f"Order is not being tracked (status: {order.tracking_status})"),
        )
    elif new_status not in _ALLOWED_TRANSITIONS[order.tracking_status]:
        raise HTTPException(
            status_code=400,
            detail=(f"Cannot move order from {order.tracking_status} to {new_status}"),
        )

    now = datetime.now(UTC)
    timestamp_column = _TIMESTAMP_COLUMNS[new_status]
    if getattr(order, timestamp_column) is None:
        setattr(order, timestamp_column, now)
    order.tracking_status = new_status
    db.add(order)
    db.commit()
    db.refresh(order)

    _publish(tenant_id, order)
    return order


def report_location(
    db: Session,
    current_user: User,
    order_id: int,
    lat: float,
    lng: float,
    source: str = "gps",
    tenant_id: int | None = None,
) -> OrderLocationUpdate:
    """Append a position ping for a tracked order and broadcast it."""
    if tenant_id is None:
        tenant_id = current_user.tenant_id

    order = _load_order(db, order_id, tenant_id)
    if order.tracking_status == TRACKING_NONE:
        raise HTTPException(
            status_code=400,
            detail="Order is not being tracked; assign it first",
        )

    update = OrderLocationUpdate(
        tenant_id=tenant_id,
        order_id=order.id,
        lat=lat,
        lng=lng,
        location=(lat, lng),
        source=source,
    )
    db.add(update)
    db.commit()
    db.refresh(update)

    _publish(tenant_id, order, lat=lat, lng=lng)
    return update


def active_tracked_orders(db: Session, tenant_id: int, limit: int = 100) -> list:
    """Orders currently being tracked, newest assignment first, with their
    latest position eagerly loaded."""
    from sqlalchemy.orm import selectinload

    return (
        db.query(Order)
        .options(selectinload(Order.location_updates))
        .filter(
            Order.tenant_id == tenant_id,
            Order.tracking_status != TRACKING_NONE,
        )
        .order_by(Order.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )


def nearest_orders(
    db: Session,
    tenant_id: int,
    lat: float,
    lng: float,
    radius_m: float,
    limit: int = 20,
) -> list:
    """Orders with a destination within ``radius_m`` of ``(lat, lng)``.

    Uses earthdistance (great-circle) over the destination coordinates;
    GiST-accelerated on ``destination`` for KNN ordering. Returns orders
    with a ``distance_m`` attribute.
    """
    sql = text(
        """
        SELECT o.*,
               earth_distance(
                   ll_to_earth(:lat, :lng),
                   ll_to_earth(o.destination_lat, o.destination_lng)
               ) AS distance_m
        FROM orders o
        WHERE o.tenant_id = :tenant_id
          AND o.destination_lat IS NOT NULL
          AND o.destination_lng IS NOT NULL
          AND o.tracking_status <> 'none'
          AND earth_distance(
                  ll_to_earth(:lat, :lng),
                  ll_to_earth(o.destination_lat, o.destination_lng)
              ) <= :radius_m
        ORDER BY o.destination <-> point(:lng, :lat)
        LIMIT :limit
        """
    )
    rows = (
        db.execute(
            sql,
            {
                "lat": lat,
                "lng": lng,
                "tenant_id": tenant_id,
                "radius_m": radius_m,
                "limit": limit,
            },
        )
        .mappings()
        .all()
    )
    orders = []
    for row in rows:
        order = db.query(Order).filter(Order.id == row["id"]).first()
        order.distance_m = row["distance_m"]
        orders.append(order)
    return orders
