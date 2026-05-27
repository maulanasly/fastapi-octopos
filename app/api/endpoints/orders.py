from datetime import datetime, timezone
from typing import List

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.customer import Customer, LoyaltyTransaction
from app.models.drawer import DrawerSession
from app.models.order import Order, OrderItem
from app.models.payment import Payment
from app.models.product import Product
from app.models.promotion import Promotion
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.order import Order as OrderSchema
from app.schemas.order import OrderCreate
from app.schemas.payment import Payment as PaymentSchema
from app.schemas.payment import PaymentCreate

router = APIRouter()


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


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

    total_amount = 0.0
    subtotal_amount = 0.0
    discount_amount = 0.0
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

        unit_price = product.price
        line_total = unit_price * item.quantity
        total_amount += line_total
        subtotal_amount += line_total

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
        if subtotal_amount < promotion.min_order_amount:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Order does not meet minimum amount for promotion. "
                    f"Required: {promotion.min_order_amount}"
                ),
            )

        if promotion.applies_to == "order":
            eligible_amount = subtotal_amount
        elif promotion.applies_to == "product":
            eligible_amount = sum(
                movement_input["line_total"]
                for movement_input in movement_inputs
                if movement_input["product_id"] == promotion.product_id
            )
            if eligible_amount <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Promotion does not apply: qualifying product not found in order",
                )
        elif promotion.applies_to == "category":
            eligible_amount = sum(
                movement_input["line_total"]
                for movement_input in movement_inputs
                if movement_input["category_id"] == promotion.category_id
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
            discount_amount = eligible_amount * (promotion.discount_value / 100.0)
        elif promotion.discount_type == "fixed":
            discount_amount = promotion.discount_value
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid promotion discount type: {promotion.discount_type}",
            )

        if promotion.max_discount_amount is not None:
            discount_amount = min(discount_amount, promotion.max_discount_amount)
        discount_amount = min(discount_amount, eligible_amount, total_amount)
        if discount_amount <= 0:
            raise HTTPException(status_code=400, detail="Promotion discount is zero")

        total_amount -= discount_amount
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
        total_amount -= float(redeemed_points)

    order = Order(
        user_id=current_user.id,
        customer_id=order_in.customer_id,
        promotion_id=promotion.id if promotion else None,
        drawer_session_id=drawer_session_id,
        idempotency_key=order_in.idempotency_key,
        subtotal_amount=subtotal_amount,
        discount_amount=discount_amount,
        total_amount=total_amount,
        redeemed_points=redeemed_points,
        status="pending",
    )
    db.add(order)
    db.flush()  # To get the order.id
    for db_item in db_items:
        db_item.order_id = order.id
        db.add(db_item)
    db.flush()

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

    if order.drawer_session_id:
        drawer = (
            db.query(DrawerSession)
            .filter(DrawerSession.id == order.drawer_session_id)
            .first()
        )
        if drawer and drawer.status != "open":
            raise HTTPException(
                status_code=400,
                detail="Cannot add payment to an order from a closed drawer session",
            )

    if order.status in ("cancelled", "completed"):
        raise HTTPException(
            status_code=400, detail=f"Cannot add payment to a {order.status} order"
        )

    payment = Payment(
        order_id=order.id,
        user_id=current_user.id,
        idempotency_key=payment_in.idempotency_key,
        payment_method=payment_in.payment_method,
        amount=payment_in.amount,
    )
    db.add(payment)
    db.flush()

    # After flush, the new payment is already present in order.payments
    total_paid = sum(p.amount for p in order.payments)

    # Update order status if fully paid
    if total_paid >= order.total_amount:
        order.status = "completed"
        db.add(order)
        if order.customer_id:
            customer = (
                db.query(Customer).filter(Customer.id == order.customer_id).first()
            )
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

    db.commit()
    db.refresh(payment)
    return payment


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

    if order.drawer_session_id:
        drawer = (
            db.query(DrawerSession)
            .filter(DrawerSession.id == order.drawer_session_id)
            .first()
        )
        if drawer and drawer.status != "open":
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel an order from a closed drawer session",
            )

    # Restore stock for all items in the order
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            quantity_before = product.stock_quantity
            product.stock_quantity += item.quantity
            db.add(product)
            db.add(
                StockMovement(
                    product_id=product.id,
                    user_id=current_user.id,
                    order_id=order.id,
                    order_item_id=item.id,
                    movement_type="order_cancel",
                    quantity_before=quantity_before,
                    quantity_delta=item.quantity,
                    quantity_after=product.stock_quantity,
                    note="Stock restored by order cancellation",
                )
            )

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

    order.status = "cancelled"
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
