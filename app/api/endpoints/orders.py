from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_active_user,
    has_permission,
    require_permissions,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.money import money_to_float, quantize_money, to_decimal
from app.core.validation import validate_drawer_session_status
from app.models.customer import Customer, LoyaltyTransaction
from app.models.drawer import DrawerSession
from app.models.order import Order, OrderItem
from app.models.payment import Payment
from app.models.product import Product
from app.models.promotion import Promotion
from app.models.stock_movement import StockMovement
from app.models.tax import OrderTaxLine, TaxRule
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

router = APIRouter()


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _is_reservation_expired(order: Order) -> bool:
    if order.reservation_status != "reserved":
        return False
    if order.reservation_expires_at is None:
        return False
    return _as_utc(order.reservation_expires_at) <= datetime.now(timezone.utc)


def _normalize_payment_method(payment_method: str) -> str:
    return payment_method.strip().lower()


# Wrapper using the shared validation helper
def _validate_drawer_session_status(db: Session, order: Order) -> None:
    """Validate that the drawer session for an order is still open (for payments)."""
    validate_drawer_session_status(db=db, order=order, action="add payment to")


def _calculate_settlement_totals(
    db: Session, order: Order
) -> tuple[Decimal, Decimal, Decimal]:
    total_paid_raw = (
        db.query(func.coalesce(func.sum(Payment.amount), 0.0))
        .filter(Payment.order_id == order.id)
        .scalar()
    )
    total_paid = quantize_money(total_paid_raw)
    order_total = quantize_money(order.total_amount)
    applied_paid_amount = min(total_paid, order_total)
    change_amount = quantize_money(max(total_paid - order_total, Decimal("0")))
    remaining_amount = quantize_money(
        max(order_total - applied_paid_amount, Decimal("0"))
    )
    return applied_paid_amount, change_amount, remaining_amount


def _sync_order_settlement(db: Session, order: Order) -> None:
    paid_amount, change_amount, remaining_amount = _calculate_settlement_totals(
        db, order
    )
    order.paid_amount = paid_amount
    order.change_amount = change_amount
    order.remaining_amount = remaining_amount


def _is_tax_rule_active(rule: TaxRule, now: datetime) -> bool:
    if not rule.is_active:
        return False
    if rule.starts_at and _as_utc(rule.starts_at) > now:
        return False
    if rule.ends_at and _as_utc(rule.ends_at) < now:
        return False
    return True


def _get_scope_subtotal(rule: TaxRule, movement_inputs: list[dict]) -> Decimal:
    if rule.tax_scope == "order":
        return quantize_money(
            sum(to_decimal(item["line_total"]) for item in movement_inputs)
        )
    if rule.tax_scope == "product":
        return quantize_money(
            sum(
                to_decimal(item["line_total"])
                for item in movement_inputs
                if item["product_id"] == rule.product_id
            )
        )
    if rule.tax_scope == "category":
        return quantize_money(
            sum(
                to_decimal(item["line_total"])
                for item in movement_inputs
                if item["category_id"] == rule.category_id
            )
        )
    return Decimal("0")


def _calculate_order_taxes(
    db: Session,
    movement_inputs: list[dict],
    taxable_base_amount: Decimal,
    now: datetime,
) -> tuple[list[dict], Decimal, Decimal]:
    active_rules = db.query(TaxRule).filter(TaxRule.is_active.is_(True)).all()
    subtotal = quantize_money(
        sum(to_decimal(item["line_total"]) for item in movement_inputs)
    )
    net_ratio = taxable_base_amount / subtotal if subtotal > 0 else Decimal("0")

    tax_lines: list[dict] = []
    exclusive_tax_total = Decimal("0")
    for rule in active_rules:
        if not _is_tax_rule_active(rule, now):
            continue

        scope_subtotal = _get_scope_subtotal(rule, movement_inputs)
        if scope_subtotal <= 0:
            continue

        scoped_taxable_base = quantize_money(scope_subtotal * net_ratio)
        if scoped_taxable_base <= 0:
            continue

        rule_rate = to_decimal(rule.rate)
        if rule.tax_mode == "inclusive":
            tax_amount = quantize_money(
                scoped_taxable_base * (rule_rate / (Decimal("100") + rule_rate))
                if rule_rate > 0
                else Decimal("0")
            )
        else:
            tax_amount = quantize_money(
                scoped_taxable_base * (rule_rate / Decimal("100"))
            )
            exclusive_tax_total = quantize_money(exclusive_tax_total + tax_amount)

        tax_lines.append(
            {
                "tax_rule_id": rule.id,
                "tax_name": rule.name,
                "tax_scope": rule.tax_scope,
                "tax_mode": rule.tax_mode,
                "tax_rate": rule_rate,
                "taxable_base": scoped_taxable_base,
                "tax_amount": tax_amount,
            }
        )

    tax_total_amount = quantize_money(
        sum(to_decimal(line["tax_amount"]) for line in tax_lines)
    )
    grand_total_amount = quantize_money(taxable_base_amount + exclusive_tax_total)
    return tax_lines, tax_total_amount, grand_total_amount


def _complete_order_if_paid(db: Session, order: Order) -> None:
    if order.remaining_amount > 0:
        return

    order.status = "completed"
    order.reservation_status = "committed"
    order.reservation_expires_at = None
    db.add(order)
    if order.customer_id:
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if customer:
            existing_earn = (
                db.query(LoyaltyTransaction)
                .filter(
                    LoyaltyTransaction.order_id == order.id,
                    LoyaltyTransaction.customer_id == customer.id,
                    LoyaltyTransaction.transaction_type == "earn",
                )
                .first()
            )
            if not existing_earn:
                earned_points = int(order.total_amount)
                if earned_points > 0:
                    customer.points_balance += earned_points
                    db.add(customer)
                    db.add(
                        LoyaltyTransaction(
                            customer_id=customer.id,
                            order_id=order.id,
                            transaction_type="earn",
                            points_delta=earned_points,
                            balance_after=customer.points_balance,
                            note="Points earned on completed order",
                        )
                    )


def _restore_order_stock(
    db: Session,
    order: Order,
    user_id: int,
    movement_type: str,
    note: str,
):
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            quantity_before = product.stock_quantity
            product.stock_quantity += item.quantity
            db.add(product)
            db.add(
                StockMovement(
                    product_id=product.id,
                    user_id=user_id,
                    order_id=order.id,
                    order_item_id=item.id,
                    movement_type=movement_type,
                    quantity_before=quantity_before,
                    quantity_delta=item.quantity,
                    quantity_after=product.stock_quantity,
                    note=note,
                )
            )


def _revert_order_customer_and_promotion_effects(
    db: Session,
    order: Order,
):
    if order.customer_id:
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if customer:
            if order.redeemed_points > 0:
                customer.points_balance += order.redeemed_points
                db.add(
                    LoyaltyTransaction(
                        customer_id=customer.id,
                        order_id=order.id,
                        transaction_type="adjust",
                        points_delta=order.redeemed_points,
                        balance_after=customer.points_balance,
                        note="Redeemed points restored due to order cancellation",
                    )
                )

            earned_points_total = (
                db.query(func.coalesce(func.sum(LoyaltyTransaction.points_delta), 0))
                .filter(
                    LoyaltyTransaction.order_id == order.id,
                    LoyaltyTransaction.customer_id == customer.id,
                    LoyaltyTransaction.transaction_type == "earn",
                )
                .scalar()
            )
            earned_points = int(earned_points_total or 0)
            if earned_points > 0:
                customer.points_balance -= earned_points
                db.add(
                    LoyaltyTransaction(
                        customer_id=customer.id,
                        order_id=order.id,
                        transaction_type="adjust",
                        points_delta=-earned_points,
                        balance_after=customer.points_balance,
                        note="Earned points reversed due to order cancellation",
                    )
                )
            db.add(customer)

    if order.promotion_id:
        promotion = (
            db.query(Promotion).filter(Promotion.id == order.promotion_id).first()
        )
        if promotion and promotion.usage_count > 0:
            promotion.usage_count -= 1
            db.add(promotion)


def _release_order_reservation(
    db: Session,
    order: Order,
    user_id: int,
    movement_type: str,
    note: str,
):
    _restore_order_stock(
        db=db,
        order=order,
        user_id=user_id,
        movement_type=movement_type,
        note=note,
    )
    _revert_order_customer_and_promotion_effects(db=db, order=order)
    order.status = "cancelled"
    order.reservation_status = "released"
    order.reservation_expires_at = None
    order.paid_amount = Decimal("0")
    order.change_amount = Decimal("0")
    order.remaining_amount = Decimal("0")
    db.add(order)


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
    if not order_in.items:
        raise HTTPException(
            status_code=400, detail="Order must contain at least one item"
        )

    if order_in.idempotency_key:
        existing_order = (
            db.query(Order)
            .filter(
                Order.user_id == current_user.id,
                Order.idempotency_key == order_in.idempotency_key,
            )
            .first()
        )
        if existing_order:
            return existing_order

    total_amount = Decimal("0")
    subtotal_amount = Decimal("0")
    discount_amount = Decimal("0")
    promotion = None
    db_items = []
    movement_inputs = []
    customer = None
    redeemed_points = 0

    if order_in.customer_id is not None:
        customer = (
            db.query(Customer).filter(Customer.id == order_in.customer_id).first()
        )
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        if not customer.is_active:
            raise HTTPException(status_code=400, detail="Customer is inactive")

    # Verify stock and calculate total amount
    for item in order_in.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=404, detail=f"Product with id {item.product_id} not found"
            )
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for product {product.name}. Available: {product.stock_quantity}",
            )

        unit_price = quantize_money(product.price)
        line_total = quantize_money(unit_price * item.quantity)
        total_amount = quantize_money(total_amount + line_total)
        subtotal_amount = quantize_money(subtotal_amount + line_total)

        # Deduct stock
        quantity_before = product.stock_quantity
        product.stock_quantity -= item.quantity
        db.add(product)

        db_items.append(
            OrderItem(
                product_id=product.id, quantity=item.quantity, unit_price=unit_price
            )
        )
        movement_inputs.append(
            {
                "product_id": product.id,
                "category_id": product.category_id,
                "line_total": line_total,
                "quantity_before": quantity_before,
                "quantity_delta": -item.quantity,
                "quantity_after": product.stock_quantity,
            }
        )

    # Verify active drawer session for the cashier
    active_drawer = (
        db.query(DrawerSession)
        .filter(
            DrawerSession.user_id == current_user.id,
            DrawerSession.status == "open",
        )
        .first()
    )
    if not active_drawer:
        raise HTTPException(
            status_code=400,
            detail="Cash drawer is not open. Please open a drawer session before placing orders.",
        )
    # Assign drawer_session_id to the new order
    drawer_session_id = active_drawer.id

    if order_in.promotion_code:
        normalized_code = order_in.promotion_code.strip().upper()
        promotion = (
            db.query(Promotion).filter(Promotion.code == normalized_code).first()
        )
        if not promotion:
            raise HTTPException(status_code=404, detail="Promotion not found")
        if not promotion.is_active:
            raise HTTPException(status_code=400, detail="Promotion is inactive")

        now = datetime.now(timezone.utc)
        if promotion.starts_at and _as_utc(promotion.starts_at) > now:
            raise HTTPException(status_code=400, detail="Promotion is not active yet")
        if promotion.ends_at and _as_utc(promotion.ends_at) < now:
            raise HTTPException(status_code=400, detail="Promotion has expired")
        usage_limit_reached = promotion.usage_limit is not None and (
            promotion.usage_count >= promotion.usage_limit
        )
        if usage_limit_reached:
            raise HTTPException(status_code=400, detail="Promotion usage limit reached")
        promotion_min_order_amount = to_decimal(promotion.min_order_amount)
        if subtotal_amount < promotion_min_order_amount:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Order does not meet minimum amount for promotion. "
                    f"Required: {promotion_min_order_amount}"
                ),
            )

        if promotion.applies_to == "order":
            eligible_amount = subtotal_amount
        elif promotion.applies_to == "product":
            eligible_amount = quantize_money(
                sum(
                    movement_input["line_total"]
                    for movement_input in movement_inputs
                    if movement_input["product_id"] == promotion.product_id
                )
            )
            if eligible_amount <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Promotion does not apply: qualifying product not found in order",
                )
        elif promotion.applies_to == "category":
            eligible_amount = quantize_money(
                sum(
                    movement_input["line_total"]
                    for movement_input in movement_inputs
                    if movement_input["category_id"] == promotion.category_id
                )
            )
            if eligible_amount <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Promotion does not apply: qualifying category not found in order",
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid promotion scope: {promotion.applies_to}",
            )

        if promotion.discount_type == "percentage":
            discount_amount = quantize_money(
                eligible_amount
                * (to_decimal(promotion.discount_value) / Decimal("100"))  # noqa: W503
            )
        elif promotion.discount_type == "fixed":
            discount_amount = quantize_money(promotion.discount_value)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid promotion discount type: {promotion.discount_type}",
            )

        if promotion.max_discount_amount is not None:
            discount_amount = min(
                discount_amount, quantize_money(promotion.max_discount_amount)
            )
        discount_amount = quantize_money(
            min(discount_amount, eligible_amount, total_amount)
        )
        if discount_amount <= 0:
            raise HTTPException(status_code=400, detail="Promotion discount is zero")

        total_amount = quantize_money(total_amount - discount_amount)
        promotion.usage_count += 1
        db.add(promotion)

    max_redeemable_points = int(total_amount)
    if order_in.redeem_points > 0:
        if not customer:
            raise HTTPException(
                status_code=400, detail="Customer is required to redeem loyalty points"
            )
        if order_in.redeem_points > customer.points_balance:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Not enough loyalty points. Available: {customer.points_balance}, "
                    f"requested: {order_in.redeem_points}"
                ),
            )
        if order_in.redeem_points > max_redeemable_points:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Redeem points exceed order total. Max redeemable points: "
                    f"{max_redeemable_points}"
                ),
            )
        redeemed_points = order_in.redeem_points
        total_amount = quantize_money(total_amount - Decimal(redeemed_points))

    taxable_base_amount = quantize_money(total_amount)
    tax_lines_data, tax_total_amount, grand_total_amount = _calculate_order_taxes(
        db=db,
        movement_inputs=movement_inputs,
        taxable_base_amount=taxable_base_amount,
        now=datetime.now(timezone.utc),
    )
    total_amount = quantize_money(grand_total_amount)

    reservation_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ORDER_RESERVATION_TIMEOUT_MINUTES
    )
    order = Order(
        user_id=current_user.id,
        customer_id=order_in.customer_id,
        promotion_id=promotion.id if promotion else None,
        drawer_session_id=drawer_session_id,
        idempotency_key=order_in.idempotency_key,
        subtotal_amount=subtotal_amount,
        discount_amount=discount_amount,
        taxable_base_amount=taxable_base_amount,
        tax_total_amount=tax_total_amount,
        grand_total_amount=grand_total_amount,
        total_amount=total_amount,
        paid_amount=Decimal("0"),
        change_amount=Decimal("0"),
        remaining_amount=total_amount,
        redeemed_points=redeemed_points,
        status="pending",
        reservation_status="reserved",
        reservation_expires_at=reservation_expires_at,
    )
    db.add(order)
    db.flush()  # To get the order.id
    for db_item in db_items:
        db_item.order_id = order.id
        db.add(db_item)
    db.flush()

    for tax_line_data in tax_lines_data:
        db.add(
            OrderTaxLine(
                order_id=order.id,
                tax_rule_id=tax_line_data["tax_rule_id"],
                tax_name=tax_line_data["tax_name"],
                tax_scope=tax_line_data["tax_scope"],
                tax_mode=tax_line_data["tax_mode"],
                tax_rate=tax_line_data["tax_rate"],
                taxable_base=tax_line_data["taxable_base"],
                tax_amount=tax_line_data["tax_amount"],
            )
        )

    for idx, db_item in enumerate(db_items):
        movement_input = movement_inputs[idx]
        db.add(
            StockMovement(
                product_id=movement_input["product_id"],
                user_id=current_user.id,
                order_id=order.id,
                order_item_id=db_item.id,
                movement_type="sale",
                quantity_before=movement_input["quantity_before"],
                quantity_delta=movement_input["quantity_delta"],
                quantity_after=movement_input["quantity_after"],
                note="Stock deducted by order creation",
            )
        )

    if customer and redeemed_points > 0:
        customer.points_balance -= redeemed_points
        db.add(customer)
        db.add(
            LoyaltyTransaction(
                customer_id=customer.id,
                order_id=order.id,
                transaction_type="redeem",
                points_delta=-redeemed_points,
                balance_after=customer.points_balance,
                note="Points redeemed on order creation",
            )
        )

    db.commit()
    db.refresh(order)
    return order


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
    if payment_in.idempotency_key:
        existing_payment = (
            db.query(Payment)
            .filter(
                Payment.user_id == current_user.id,
                Payment.idempotency_key == payment_in.idempotency_key,
            )
            .first()
        )
        if existing_payment:
            return existing_payment

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not current_user.is_superuser and order.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to add payment to this order"
        )

    _validate_drawer_session_status(db=db, order=order)

    if order.status in ("cancelled", "completed"):
        raise HTTPException(
            status_code=400, detail=f"Cannot add payment to a {order.status} order"
        )
    if order.reservation_status == "released":
        raise HTTPException(
            status_code=400, detail="Cannot add payment to an order with released stock"
        )
    if _is_reservation_expired(order):
        raise HTTPException(
            status_code=400,
            detail="Order reservation has expired. Release reservation and create a new order",
        )

    _sync_order_settlement(db=db, order=order)
    payment_method = _normalize_payment_method(payment_in.payment_method)
    payment_amount = quantize_money(payment_in.amount)
    remaining_amount = quantize_money(order.remaining_amount)
    if payment_method != "cash" and payment_amount > remaining_amount:
        raise HTTPException(
            status_code=400,
            detail="Non-cash payment amount cannot exceed remaining amount",
        )

    payment = Payment(
        order_id=order.id,
        user_id=current_user.id,
        idempotency_key=payment_in.idempotency_key,
        payment_method=payment_method,
        amount=payment_amount,
    )
    db.add(payment)
    db.flush()

    _sync_order_settlement(db=db, order=order)
    _complete_order_if_paid(db=db, order=order)

    db.commit()
    db.refresh(payment)
    return payment


@router.post("/{order_id}/payments/split", response_model=OrderSchema)
def add_split_payments_to_order(
    order_id: int,
    split_in: SplitPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not split_in.payments:
        raise HTTPException(
            status_code=400,
            detail="Split payment must contain at least one payment line",
        )

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not current_user.is_superuser and order.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to add payment to this order"
        )

    _validate_drawer_session_status(db=db, order=order)

    if order.status in ("cancelled", "completed"):
        raise HTTPException(
            status_code=400, detail=f"Cannot add payment to a {order.status} order"
        )
    if order.reservation_status == "released":
        raise HTTPException(
            status_code=400, detail="Cannot add payment to an order with released stock"
        )
    if _is_reservation_expired(order):
        raise HTTPException(
            status_code=400,
            detail="Order reservation has expired. Release reservation and create a new order",
        )

    running_total_paid = quantize_money(
        sum(to_decimal(payment.amount) for payment in order.payments)
    )
    order_total_amount = quantize_money(order.total_amount)
    for line in split_in.payments:
        payment_method = _normalize_payment_method(line.payment_method)
        line_amount = quantize_money(line.amount)
        remaining_before = quantize_money(
            max(
                order_total_amount - min(running_total_paid, order_total_amount),
                Decimal("0"),
            )
        )
        if payment_method != "cash" and line_amount > remaining_before:
            raise HTTPException(
                status_code=400,
                detail="Non-cash payment amount cannot exceed remaining amount",
            )
        running_total_paid = quantize_money(running_total_paid + line_amount)

    for line in split_in.payments:
        db.add(
            Payment(
                order_id=order.id,
                user_id=current_user.id,
                payment_method=_normalize_payment_method(line.payment_method),
                amount=quantize_money(line.amount),
            )
        )

    db.flush()
    _sync_order_settlement(db=db, order=order)
    _complete_order_if_paid(db=db, order=order)
    db.commit()
    db.refresh(order)
    return order


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

    now = datetime.now(timezone.utc)
    candidate_orders = (
        db.query(Order)
        .filter(
            Order.status == "pending",
            Order.reservation_status == "reserved",
            Order.reservation_expires_at.isnot(None),
            Order.reservation_expires_at <= now,
        )
        .all()
    )

    released_order_ids = []
    skipped_paid_order_ids = []
    for order in candidate_orders:
        total_paid = quantize_money(
            sum(to_decimal(payment.amount) for payment in order.payments)
        )
        if total_paid > 0:
            skipped_paid_order_ids.append(order.id)
            continue

        _release_order_reservation(
            db=db,
            order=order,
            user_id=current_user.id,
            movement_type="reservation_release",
            note="Stock restored by expired reservation release",
        )
        released_order_ids.append(order.id)

    db.commit()
    return ReservationReleaseSummary(
        released_count=len(released_order_ids),
        skipped_paid_count=len(skipped_paid_order_ids),
        released_order_ids=released_order_ids,
        skipped_paid_order_ids=skipped_paid_order_ids,
    )


@router.post("/{order_id}/cancel", response_model=OrderSchema)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # If not superuser, only allow cancelling their own orders
    if not current_user.is_superuser and order.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to cancel this order"
        )

    if order.status == "cancelled":
        raise HTTPException(status_code=400, detail="Order is already cancelled")

    validate_drawer_session_status(db=db, order=order, action="cancel")

    _release_order_reservation(
        db=db,
        order=order,
        user_id=current_user.id,
        movement_type="order_cancel",
        note="Stock restored by order cancellation",
    )
    db.commit()
    db.refresh(order)
    return order
