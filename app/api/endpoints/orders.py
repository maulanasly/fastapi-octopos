from typing import List

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_active_user,
    has_permission,
    require_permissions,
)
from app.core.database import get_db
from app.core.money import money_to_float, to_decimal
from app.models.order import Order
from app.models.user import User
from app.schemas.order import Order as OrderSchema
from app.schemas.order import (
    OrderCreate,
    OrderReceipt,
    ReceiptOrderItem,
    ReservationReleaseSummary,
)
from app.schemas.payment import Payment as PaymentSchema
from app.schemas.payment import PaymentCreate, SplitPaymentCreate
from app.services.orders import add_payment_to_order as add_payment_to_order_service
from app.services.orders import (
    add_split_payments_to_order as add_split_payments_to_order_service,
)
from app.services.orders import cancel_order as cancel_order_service
from app.services.orders import create_order as create_order_service
from app.services.orders import (
    release_expired_reservations as release_expired_reservations_service,
)

router = APIRouter()


@router.get("/", response_model=List[OrderSchema])
def get_orders(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    # If not superuser, only return their own orders
    if not current_user.is_superuser:
        orders = (
            db.query(Order)
            .filter(Order.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    else:
        orders = db.query(Order).offset(skip).limit(limit).all()
    return orders


@router.post("/", response_model=OrderSchema)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return create_order_service(db=db, current_user=current_user, order_in=order_in)


@router.get("/{order_id}/receipt", response_model=OrderReceipt)
def get_order_receipt(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not current_user.is_superuser and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")

    item_lines = [
        ReceiptOrderItem(
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=money_to_float(item.unit_price),
            line_total=money_to_float(to_decimal(item.unit_price) * item.quantity),
        )
        for item in order.items
    ]
    subtotal_amount = (
        money_to_float(order.subtotal_amount)
        if order.subtotal_amount is not None
        else money_to_float(sum(item.line_total for item in item_lines))
    )

    return OrderReceipt(
        order_id=order.id,
        created_at=order.created_at,
        customer_name=order.customer.name if order.customer else None,
        cashier_name=(order.user.full_name or order.user.email) if order.user else None,
        subtotal_amount=subtotal_amount,
        discount_amount=money_to_float(order.discount_amount),
        redeemed_points=int(order.redeemed_points or 0),
        taxable_base_amount=money_to_float(order.taxable_base_amount),
        tax_total_amount=money_to_float(order.tax_total_amount),
        grand_total_amount=money_to_float(order.grand_total_amount),
        total_amount=money_to_float(order.total_amount),
        paid_amount=money_to_float(order.paid_amount),
        change_amount=money_to_float(order.change_amount),
        remaining_amount=money_to_float(order.remaining_amount),
        status=order.status,
        reservation_status=order.reservation_status,
        items=item_lines,
        tax_lines=order.tax_lines,
        payments=order.payments,
    )


@router.post("/{order_id}/payments", response_model=PaymentSchema)
def add_payment_to_order(
    order_id: int,
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return add_payment_to_order_service(
        db=db,
        current_user=current_user,
        order_id=order_id,
        payment_in=payment_in,
    )


@router.post("/{order_id}/payments/split", response_model=OrderSchema)
def add_split_payments_to_order(
    order_id: int,
    split_in: SplitPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return add_split_payments_to_order_service(
        db=db,
        current_user=current_user,
        order_id=order_id,
        split_in=split_in,
    )


@router.post("/release-expired-reservations", response_model=ReservationReleaseSummary)
def release_expired_reservations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders:release_reservations")),
):
    if not has_permission(
        db=db,
        user=current_user,
        permission_code="orders:release_reservations",
    ):
        raise HTTPException(
            status_code=403,
            detail="Missing permission: orders:release_reservations",
        )

    return release_expired_reservations_service(db=db, current_user=current_user)


@router.post("/{order_id}/cancel", response_model=OrderSchema)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return cancel_order_service(db=db, current_user=current_user, order_id=order_id)
