from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.order import Order, OrderItem
from app.models.payment import Payment
from app.models.product import Product
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
        product.stock_quantity -= item.quantity
        db.add(product)

        db_items.append(
            OrderItem(
                product_id=product.id, quantity=item.quantity, unit_price=unit_price
            )
        )

    order = Order(user_id=current_user.id, total_amount=total_amount, status="pending")

    db.add(order)
    db.flush()  # To get the order.id

    for db_item in db_items:
        db_item.order_id = order.id
        db.add(db_item)

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

    payment = Payment(
        order_id=order.id,
        payment_method=payment_in.payment_method,
        amount=payment_in.amount,
    )
    db.add(payment)
    db.flush()

    # Calculate total paid
    total_paid = sum(p.amount for p in order.payments) + payment.amount

    # Update order status if fully paid
    if total_paid >= order.total_amount:
        order.status = "completed"
        db.add(order)

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

    # Restore stock for all items in the order
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock_quantity += item.quantity
            db.add(product)

    order.status = "cancelled"
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
