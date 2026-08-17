from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, require_permissions
from app.core.database import get_db
from app.models.customer import Customer, LoyaltyTransaction
from app.models.order import Order
from app.models.user import User
from app.schemas.customer import Customer as CustomerSchema
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.customer import LoyaltyTransaction as LoyaltyTransactionSchema
from app.schemas.order import Order as OrderSchema

router = APIRouter()


@router.get("/", response_model=List[CustomerSchema])
def get_customers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    return (
        db.query(Customer)
        .filter(Customer.tenant_id == current_user.tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("/", response_model=CustomerSchema)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("customers:create")),
):
    customer = Customer(**customer_in.model_dump(), tenant_id=current_user.tenant_id)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerSchema)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/{customer_id}", response_model=CustomerSchema)
def update_customer(
    customer_id: int,
    customer_in: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("customers:manage")),
):
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = customer_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
def deactivate_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("customers:manage")),
):
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer.is_active = False
    db.add(customer)
    db.commit()
    return {"ok": True}


@router.get("/{customer_id}/orders", response_model=List[OrderSchema])
def get_customer_orders(
    customer_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return (
        db.query(Order)
        .filter(
            Order.customer_id == customer_id,
            Order.tenant_id == current_user.tenant_id,
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/{customer_id}/loyalty-transactions",
    response_model=List[LoyaltyTransactionSchema],
)
def get_customer_loyalty_transactions(
    customer_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return (
        db.query(LoyaltyTransaction)
        .filter(
            LoyaltyTransaction.customer_id == customer_id,
            LoyaltyTransaction.tenant_id == current_user.tenant_id,
        )
        .order_by(LoyaltyTransaction.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
