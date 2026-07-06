from collections import defaultdict
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_current_active_user, require_permissions
from app.core.database import get_db
from app.core.validation import validate_drawer_session_status
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.refund import Refund, RefundItem
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.refund import Refund as RefundSchema
from app.schemas.refund import RefundCreate

router = APIRouter()


@router.get("/", response_model=List[RefundSchema])
def get_refunds(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    order_id: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(require_permissions("refunds:view")),
):
    query = (
        db.query(Refund).options(joinedload(Refund.items)).order_by(Refund.id.desc())
    )

    if not current_user.is_superuser:
        query = query.filter(Refund.user_id == current_user.id)
    if order_id:
        query = query.filter(Refund.order_id == order_id)

    return query.offset(skip).limit(limit).all()


@router.get("/{refund_id}", response_model=RefundSchema)
def get_refund(
    refund_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("refunds:view")),
):
    refund = (
        db.query(Refund)
        .options(joinedload(Refund.items))
        .filter(Refund.id == refund_id)
        .first()
    )
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")

    if not current_user.is_superuser and refund.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this refund"
        )

    return refund


@router.post("/", response_model=RefundSchema)
def create_refund(
    refund_in: RefundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("refunds:create")),
):
    if not refund_in.items:
        raise HTTPException(
            status_code=400, detail="Refund must contain at least one item"
        )

    if refund_in.idempotency_key:
        existing_refund = (
            db.query(Refund)
            .filter(
                Refund.user_id == current_user.id,
                Refund.idempotency_key == refund_in.idempotency_key,
            )
            .first()
        )
        if existing_refund:
            return existing_refund

    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == refund_in.order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not current_user.is_superuser and order.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to refund this order"
        )

    if order.status != "completed":
        raise HTTPException(
            status_code=400, detail="Only completed orders can be refunded"
        )

    validate_drawer_session_status(db=db, order=order, action="refund")

    item_quantities = defaultdict(int)
    for item in refund_in.items:
        item_quantities[item.order_item_id] += item.quantity

    requested_item_ids = list(item_quantities.keys())
    order_item_map = {item.id: item for item in order.items}

    missing_order_item_ids = [
        item_id for item_id in requested_item_ids if item_id not in order_item_map
    ]
    if missing_order_item_ids:
        missing_items_text = ", ".join(
            str(item_id) for item_id in missing_order_item_ids
        )
        raise HTTPException(
            status_code=400,
            detail=f"Order item(s) not found in order: {missing_items_text}",
        )

    already_refunded = dict(
        db.query(
            RefundItem.order_item_id, func.coalesce(func.sum(RefundItem.quantity), 0)
        )
        .join(Refund, RefundItem.refund_id == Refund.id)
        .filter(
            Refund.order_id == order.id,
            RefundItem.order_item_id.in_(requested_item_ids),
        )
        .group_by(RefundItem.order_item_id)
        .all()
    )

    refund_items: List[RefundItem] = []
    movement_inputs = []
    total_amount = 0.0

    for order_item_id, quantity in item_quantities.items():
        order_item: OrderItem = order_item_map[order_item_id]
        previously_refunded = int(already_refunded.get(order_item_id, 0))
        refundable_quantity = order_item.quantity - previously_refunded

        if quantity > refundable_quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Refund quantity exceeds refundable quantity for order item "
                    f"{order_item_id}. Requested: {quantity}, available: {refundable_quantity}"
                ),
            )

        product = db.query(Product).filter(Product.id == order_item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with id {order_item.product_id} not found",
            )

        quantity_before = product.stock_quantity
        product.stock_quantity += quantity
        db.add(product)

        total_amount += float(order_item.unit_price) * quantity
        refund_items.append(
            RefundItem(
                order_item_id=order_item.id,
                product_id=order_item.product_id,
                quantity=quantity,
                unit_price=order_item.unit_price,
            )
        )
        movement_inputs.append(
            {
                "product_id": order_item.product_id,
                "order_item_id": order_item.id,
                "quantity_before": quantity_before,
                "quantity_delta": quantity,
                "quantity_after": product.stock_quantity,
            }
        )

    refund = Refund(
        order_id=order.id,
        user_id=current_user.id,
        idempotency_key=refund_in.idempotency_key,
        reason=refund_in.reason,
        total_amount=total_amount,
    )
    db.add(refund)
    db.flush()

    for refund_item in refund_items:
        refund_item.refund_id = refund.id
        db.add(refund_item)

    for movement_input in movement_inputs:
        db.add(
            StockMovement(
                product_id=movement_input["product_id"],
                user_id=current_user.id,
                order_id=order.id,
                order_item_id=movement_input["order_item_id"],
                refund_id=refund.id,
                movement_type="refund",
                quantity_before=movement_input["quantity_before"],
                quantity_delta=movement_input["quantity_delta"],
                quantity_after=movement_input["quantity_after"],
                note="Stock restored by refund",
            )
        )

    db.commit()

    return (
        db.query(Refund)
        .options(joinedload(Refund.items))
        .filter(Refund.id == refund.id)
        .first()
    )
