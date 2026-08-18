"""Order tracking endpoints: status transitions, location pings, live list.

All routes are tenant-scoped and require ``orders:track`` (viewing the
active list requires ``orders:manage`` — the back-office sees trips, the
field worker drives them). Location pings are append-only history and are
broadcast over the shared SSE hub as ``event: tracking``.
"""

from datetime import datetime

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_permissions
from app.models.user import User
from app.schemas.order import LocationUpdate
from app.schemas.order import Order as OrderSchema
from app.services.tracking import (
    active_tracked_orders,
    nearest_orders,
    report_location,
    transition_tracking_status,
)

router = APIRouter()


class TrackingStatusIn(BaseModel):
    status: str = Field(..., description="assigned, en_route or on_site")


class LocationIn(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    source: str = Field("gps", pattern="^(gps|manual|offline)$")


class TrackedOrder(BaseModel):
    order_id: int
    status: str
    tracking_status: str
    destination_address: str | None = None
    destination_lat: float | None = None
    destination_lng: float | None = None
    latest_location: LocationUpdate | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[TrackedOrder])
def get_active_tracking(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders:track")),
):
    """All orders currently being tracked (with latest positions)."""
    orders = active_tracked_orders(db, current_user.tenant_id)
    return [
        {
            "order_id": o.id,
            "status": o.status,
            "tracking_status": o.tracking_status,
            "destination_address": o.destination_address,
            "destination_lat": o.destination_lat,
            "destination_lng": o.destination_lng,
            "latest_location": o.latest_location,
            "created_at": o.created_at,
        }
        for o in orders
    ]


@router.post("/{order_id}/status", response_model=OrderSchema)
def update_tracking_status(
    order_id: int,
    payload: TrackingStatusIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders:track")),
):
    """Advance tracking: assigned -> en_route -> on_site (strict)."""
    order = transition_tracking_status(db, current_user, order_id, payload.status)
    return order


@router.post("/{order_id}/location", response_model=LocationUpdate)
def post_location(
    order_id: int,
    payload: LocationIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders:track")),
):
    """Append a position ping for a tracked order."""
    update = report_location(
        db, current_user, order_id, payload.lat, payload.lng, payload.source
    )
    return LocationUpdate(
        lat=update.lat,
        lng=update.lng,
        source=update.source,
        created_at=update.created_at,
    )


@router.get("/nearest")
def get_nearest_orders(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10, ge=0.1, le=2000),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders:track")),
):
    """Orders with destinations within ``radius_km`` of a point, nearest
    first (great-circle distance via earthdistance)."""
    orders = nearest_orders(
        db,
        current_user.tenant_id,
        lat,
        lng,
        radius_m=radius_km * 1000.0,
        limit=limit,
    )
    return [
        {
            "order_id": o.id,
            "tracking_status": o.tracking_status,
            "destination_address": o.destination_address,
            "distance_m": round(o.distance_m, 1),
        }
        for o in orders
    ]
