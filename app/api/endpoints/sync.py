import json
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.sync_event import SyncEventLog
from app.models.user import User
from app.schemas.order import OrderCreate
from app.schemas.payment import PaymentCreate
from app.schemas.refund import RefundCreate
from app.schemas.sync import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncEventIn,
    SyncEventResult,
)
from app.services.orders import add_payment_to_order, create_order
from app.services.refunds import create_refund

router = APIRouter()


def _process_event(
    event: SyncEventIn,
    db: Session,
    current_user: User,
) -> tuple[str, int]:
    payload: Dict[str, Any] = dict(event.payload)

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

    raise HTTPException(
        status_code=400,
        detail=(
            "Unsupported event_type. Supported values: "
            "order_create, order_add_payment, refund_create"
        ),
    )


@router.post("/events/batch", response_model=SyncBatchResponse)
def sync_events_batch(
    batch_in: SyncBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    results: List[SyncEventResult] = []

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
