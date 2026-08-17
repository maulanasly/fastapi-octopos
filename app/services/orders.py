from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.money import quantize_money, to_decimal
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
from app.schemas.order import OrderCreate, ReservationReleaseSummary
from app.schemas.payment import PaymentCreate, SplitPaymentCreate


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


def _validate_drawer_session_status(db: Session, order: Order) -> None:
    """Validate that the drawer session for an order is still open (for payments)."""
    validate_drawer_session_status(db=db, order=order, action="add payment to")


def _calculate_settlement_totals(
    db: Session, order: Order
) -> tuple[Decimal, Decimal, Decimal]:
    total_paid_raw = (
        db.query(func.coalesce(func.sum(Payment.amount), 0.0))
        .filter(
            Payment.order_id == order.id,
            Payment.tenant_id == order.tenant_id,
        )
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
    tenant_id: int,
    now: datetime,
) -> tuple[list[dict], Decimal, Decimal]:
    active_rules = (
        db.query(TaxRule)
        .filter(TaxRule.is_active.is_(True), TaxRule.tenant_id == tenant_id)
        .all()
    )
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
    if order.serving_status == "none":
        order.serving_status = "queued"
    db.add(order)
    if order.customer_id:
        customer = (
            db.query(Customer)
            .filter(
                Customer.id == order.customer_id,
                Customer.tenant_id == order.tenant_id,
            )
            .first()
        )
        if customer:
            existing_earn = (
                db.query(LoyaltyTransaction)
                .filter(
                    LoyaltyTransaction.order_id == order.id,
                    LoyaltyTransaction.customer_id == customer.id,
                    LoyaltyTransaction.transaction_type == "earn",
                    LoyaltyTransaction.tenant_id == order.tenant_id,
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
                            tenant_id=order.tenant_id,
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
        product = (
            db.query(Product)
            .filter(
                Product.id == item.product_id,
                Product.tenant_id == order.tenant_id,
            )
            .with_for_update()
            .first()
        )
        if product:
            quantity_before = product.stock_quantity
            product.stock_quantity += item.quantity
            db.add(product)
            db.add(
                StockMovement(
                    product_id=product.id,
                    tenant_id=order.tenant_id,
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
        customer = (
            db.query(Customer)
            .filter(
                Customer.id == order.customer_id,
                Customer.tenant_id == order.tenant_id,
            )
            .first()
        )
        if customer:
            if order.redeemed_points > 0:
                customer.points_balance += order.redeemed_points
                db.add(
                    LoyaltyTransaction(
                        customer_id=customer.id,
                        tenant_id=order.tenant_id,
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
                    LoyaltyTransaction.tenant_id == order.tenant_id,
                )
                .scalar()
            )
            earned_points = int(earned_points_total or 0)
            if earned_points > 0:
                customer.points_balance -= earned_points
                db.add(
                    LoyaltyTransaction(
                        customer_id=customer.id,
                        tenant_id=order.tenant_id,
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
            db.query(Promotion)
            .filter(
                Promotion.id == order.promotion_id,
                Promotion.tenant_id == order.tenant_id,
            )
            .first()
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


def create_order(
    db: Session,
    current_user: User,
    order_in: OrderCreate,
    tenant_id: Optional[int] = None,
) -> Order:
    if tenant_id is None:
        tenant_id = current_user.tenant_id

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
                Order.tenant_id == tenant_id,
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
            db.query(Customer)
            .filter(
                Customer.id == order_in.customer_id,
                Customer.tenant_id == tenant_id,
            )
            .with_for_update()
            .first()
        )
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        if not customer.is_active:
            raise HTTPException(status_code=400, detail="Customer is inactive")

    # Verify stock and calculate total amount. Products are locked in
    # ascending id order so concurrent carts with overlapping products
    # cannot deadlock each other (lock-ordering).
    for item in sorted(order_in.items, key=lambda it: it.product_id):
        product = (
            db.query(Product)
            .filter(
                Product.id == item.product_id,
                Product.tenant_id == tenant_id,
            )
            .with_for_update()
            .first()
        )
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
                product_id=product.id,
                tenant_id=tenant_id,
                quantity=item.quantity,
                unit_price=unit_price,
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
            DrawerSession.tenant_id == tenant_id,
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
            db.query(Promotion)
            .filter(
                Promotion.code == normalized_code,
                Promotion.tenant_id == tenant_id,
            )
            .with_for_update()
            .first()
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
        tenant_id=tenant_id,
        now=datetime.now(timezone.utc),
    )
    total_amount = quantize_money(grand_total_amount)

    reservation_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ORDER_RESERVATION_TIMEOUT_MINUTES
    )
    order = Order(
        user_id=current_user.id,
        tenant_id=tenant_id,
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
                tenant_id=tenant_id,
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
                tenant_id=tenant_id,
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
                tenant_id=tenant_id,
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


def add_payment_to_order(
    db: Session,
    current_user: User,
    order_id: int,
    payment_in: PaymentCreate,
    tenant_id: Optional[int] = None,
) -> Payment:
    if tenant_id is None:
        tenant_id = current_user.tenant_id

    if payment_in.idempotency_key:
        existing_payment = (
            db.query(Payment)
            .filter(
                Payment.user_id == current_user.id,
                Payment.idempotency_key == payment_in.idempotency_key,
                Payment.tenant_id == tenant_id,
            )
            .first()
        )
        if existing_payment:
            return existing_payment

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
        tenant_id=tenant_id,
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


def add_split_payments_to_order(
    db: Session,
    current_user: User,
    order_id: int,
    split_in: SplitPaymentCreate,
    tenant_id: Optional[int] = None,
) -> Order:
    if tenant_id is None:
        tenant_id = current_user.tenant_id

    if not split_in.payments:
        raise HTTPException(
            status_code=400,
            detail="Split payment must contain at least one payment line",
        )

    split_keys = [
        line.idempotency_key for line in split_in.payments if line.idempotency_key
    ]
    if split_keys:
        existing_count = (
            db.query(func.count(Payment.id))
            .filter(
                Payment.user_id == current_user.id,
                Payment.idempotency_key.in_(split_keys),
                Payment.tenant_id == tenant_id,
            )
            .scalar()
        )
        if existing_count == len(split_keys):
            return (
                db.query(Order)
                .filter(
                    Order.id == order_id,
                    Order.tenant_id == tenant_id,
                )
                .first()
            )
        if existing_count > 0:
            raise HTTPException(
                status_code=409,
                detail="Split payment batch partially applied; do not retry with changed keys",
            )

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

    if not current_user.is_superuser and order.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to process payment for this order",
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
                tenant_id=tenant_id,
                user_id=current_user.id,
                payment_method=_normalize_payment_method(line.payment_method),
                amount=quantize_money(line.amount),
                idempotency_key=line.idempotency_key,
            )
        )

    db.flush()
    _sync_order_settlement(db=db, order=order)
    _complete_order_if_paid(db=db, order=order)
    db.commit()
    db.refresh(order)
    return order


def release_expired_reservations(
    db: Session,
    current_user: User,
    tenant_id: Optional[int] = None,
) -> ReservationReleaseSummary:
    if tenant_id is None:
        tenant_id = current_user.tenant_id
    return release_expired_reservations_for_user(
        db=db, user_id=current_user.id, tenant_id=tenant_id
    )


def release_expired_reservations_for_user(
    db: Session,
    user_id: int,
    tenant_id: Optional[int] = None,
) -> ReservationReleaseSummary:
    now = datetime.now(timezone.utc)
    candidate_orders = db.query(Order).filter(
        Order.status == "pending",
        Order.reservation_status == "reserved",
        Order.reservation_expires_at.isnot(None),
        Order.reservation_expires_at <= now,
    )
    if tenant_id is not None:
        candidate_orders = candidate_orders.filter(Order.tenant_id == tenant_id)
    candidate_orders = (
        candidate_orders.options(selectinload(Order.payments)).with_for_update().all()
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
            user_id=user_id,
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


def cancel_order(
    db: Session,
    current_user: User,
    order_id: int,
    tenant_id: Optional[int] = None,
) -> Order:
    if tenant_id is None:
        tenant_id = current_user.tenant_id

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
