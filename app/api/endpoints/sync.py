import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.sync_event import SyncEventLog
from app.models.user import User
from app.schemas.catalog_delta import CatalogDelta
from app.schemas.order import OrderCreate
from app.schemas.payment import PaymentCreate
from app.schemas.refund import RefundCreate
from app.schemas.sync import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncEventIn,
    SyncEventResult,
    SyncEventStatusList,
)
from app.services.orders import add_payment_to_order, create_order
from app.services.refunds import create_refund
from app.services.sync import get_catalog_delta, get_event_logs
from app.services.tracking import report_location


def _user_has_permission(db: Session, user: User, code: str) -> bool:
    """Inline RBAC check for sync replay (no FastAPI Depends available)."""
    if user.is_superuser:
        return True
    return any(code in (p.code for p in role.permissions) for role in user.roles)


router = APIRouter()


def _process_event(
    event: SyncEventIn,
    db: Session,
    current_user: User,
) -> tuple[str, int]:
    payload: dict[str, Any] = dict(event.payload)

    if event.event_type == "order_create":
        payload["idempotency_key"] = event.idempotency_key
        order_in = OrderCreate(**payload)
        order = create_order(order_in=order_in, db=db, current_user=current_user)
        return "order", order.id

    if event.event_type == "order_add_payment":
        if "order_id" not in payload:
            raise HTTPException(
                status_code=400, detail="order_id is required in payload"
            )
        order_id = int(payload["order_id"])
        payment_payload = {k: v for k, v in payload.items() if k != "order_id"}
        payment_payload["idempotency_key"] = event.idempotency_key
        payment_in = PaymentCreate(**payment_payload)
        payment = add_payment_to_order(
            order_id=order_id, payment_in=payment_in, db=db, current_user=current_user
        )
        return "payment", payment.id

    if event.event_type == "refund_create":
        payload["idempotency_key"] = event.idempotency_key
        refund_in = RefundCreate(**payload)
        refund = create_refund(refund_in=refund_in, db=db, current_user=current_user)
        return "refund", refund.id

    if event.event_type == "order_location_update":
        if not _user_has_permission(db, current_user, "orders:track"):
            raise HTTPException(
                status_code=403, detail="Not authorized to report locations"
            )
        if not all(k in payload for k in ("order_id", "lat", "lng")):
            raise HTTPException(
                status_code=400,
                detail="order_id, lat and lng are required in payload",
            )
        update = report_location(
            db=db,
            current_user=current_user,
            order_id=int(payload["order_id"]),
            lat=float(payload["lat"]),
            lng=float(payload["lng"]),
            source=str(payload.get("source", "offline")),
        )
        return "order_location_update", update.id

    raise HTTPException(
        status_code=400,
        detail=(
            "Unsupported event_type. Supported values: "
            "order_create, order_add_payment, refund_create, order_location_update"
        ),
    )


@router.get("/catalog", response_model=CatalogDelta)
def get_sync_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    since: datetime | None = Query(
        None, description="Only rows updated after this ISO timestamp"
    ),
):
    """Pull-side delta sync: catalog changes since the given watermark.

    First-time terminals omit ``since`` to receive the full catalog.
    """
    return get_catalog_delta(db=db, since=since, tenant_id=current_user.tenant_id)


@router.get("/events", response_model=SyncEventStatusList)
def get_sync_event_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    user_id: int | None = Query(None, description="Filter by terminal user id"),
    status: str | None = Query(None, description="Filter by event status"),
    skip: int = 0,
    limit: int = 100,
):
    """Status of processed offline events (per terminal)."""
    if user_id is not None and (
        not current_user.is_superuser and user_id != current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to view other users' events"
        )
    return get_event_logs(
        db=db,
        user_id=user_id,
        status=status,
        skip=skip,
        limit=limit,
        tenant_id=current_user.tenant_id,
    )


@router.post("/events/batch", response_model=SyncBatchResponse)
def sync_events_batch(
    batch_in: SyncBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    results: list[SyncEventResult] = []

    for event in batch_in.events:
        existing = (
            db.query(SyncEventLog)
            .filter(
                SyncEventLog.user_id == current_user.id,
                SyncEventLog.client_event_id == event.client_event_id,
                SyncEventLog.event_type == event.event_type,
            )
            .first()
        )
        if existing:
            results.append(
                SyncEventResult(
                    client_event_id=event.client_event_id,
                    event_type=event.event_type,
                    status="duplicate",
                    resource_type=existing.resource_type,
                    resource_id=existing.resource_id,
                    message=existing.message,
                )
            )
            continue

        try:
            resource_type, resource_id = _process_event(
                event=event, db=db, current_user=current_user
            )
            db.add(
                SyncEventLog(
                    user_id=current_user.id,
                    tenant_id=current_user.tenant_id,
                    client_event_id=event.client_event_id,
                    event_type=event.event_type,
                    idempotency_key=event.idempotency_key,
                    status="success",
                    resource_type=resource_type,
                    resource_id=resource_id,
                    payload_json=json.dumps(event.payload),
                    message="Processed successfully",
                )
            )
            db.commit()

            results.append(
                SyncEventResult(
                    client_event_id=event.client_event_id,
                    event_type=event.event_type,
                    status="success",
                    resource_type=resource_type,
                    resource_id=resource_id,
                    message="Processed successfully",
                )
            )
        except (HTTPException, ValidationError) as exc:
            db.rollback()

            message = (
                exc.detail  # type: ignore[attr-defined]
                if isinstance(exc, HTTPException)
                else str(exc)
            )
            db.add(
                SyncEventLog(
                    user_id=current_user.id,
                    tenant_id=current_user.tenant_id,
                    client_event_id=event.client_event_id,
                    event_type=event.event_type,
                    idempotency_key=event.idempotency_key,
                    status="failed",
                    payload_json=json.dumps(event.payload),
                    message=str(message),
                )
            )
            db.commit()

            results.append(
                SyncEventResult(
                    client_event_id=event.client_event_id,
                    event_type=event.event_type,
                    status="failed",
                    message=str(message),
                )
            )
        except IntegrityError:
            db.rollback()
            existing_after_conflict = (
                db.query(SyncEventLog)
                .filter(
                    SyncEventLog.user_id == current_user.id,
                    SyncEventLog.client_event_id == event.client_event_id,
                    SyncEventLog.event_type == event.event_type,
                )
                .first()
            )
            if existing_after_conflict:
                results.append(
                    SyncEventResult(
                        client_event_id=event.client_event_id,
                        event_type=event.event_type,
                        status="duplicate",
                        resource_type=existing_after_conflict.resource_type,
                        resource_id=existing_after_conflict.resource_id,
                        message=existing_after_conflict.message,
                    )
                )
            else:
                results.append(
                    SyncEventResult(
                        client_event_id=event.client_event_id,
                        event_type=event.event_type,
                        status="failed",
                        message="Sync conflict while writing event log",
                    )
                )

    return SyncBatchResponse(results=results)
