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
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.order import Order as OrderSchema
from app.schemas.order import OrderCreate
from app.schemas.payment import Payment as PaymentSchema
from app.schemas.payment import PaymentCreate

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
    if not order_in.items:
        raise HTTPException(
            status_code=400, detail="Order must contain at least one item"
        )

    total_amount = 0.0
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
        total_amount += unit_price * item.quantity

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
        drawer_session_id=drawer_session_id,
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

    order.status = "cancelled"
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
