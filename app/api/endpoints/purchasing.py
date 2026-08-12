from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import (
    get_current_active_user,
    has_permission,
    require_permissions,
)
from app.core.database import get_db
from app.models.product import Product
from app.models.purchase import PurchaseInvoice, PurchaseOrder, Supplier
from app.models.user import User
from app.schemas.purchase import PurchaseInvoice as PurchaseInvoiceSchema
from app.schemas.purchase import PurchaseInvoiceCreate, PurchaseInvoiceReviewAction
from app.schemas.purchase import PurchaseOrder as PurchaseOrderSchema
from app.schemas.purchase import PurchaseOrderCreate, PurchaseOrderReceive
from app.schemas.purchase import Supplier as SupplierSchema
from app.schemas.purchase import SupplierCreate, SupplierUpdate
from app.schemas.replenishment import PurchaseOrderFromSuggestionsCreate
from app.services.purchasing import _get_purchase_invoice_for_user
from app.services.purchasing import (
    approve_purchase_invoice as approve_purchase_invoice_service,
)
from app.services.purchasing import (
    cancel_purchase_order as cancel_purchase_order_service,
)
from app.services.purchasing import (
    create_purchase_invoice as create_purchase_invoice_service,
)
from app.services.purchasing import (
    create_purchase_order as create_purchase_order_service,
)
from app.services.purchasing import (
    create_purchase_order_from_replenishment as create_purchase_order_from_replenishment_service,
)
from app.services.purchasing import (
    mark_purchase_order_ordered as mark_purchase_order_ordered_service,
)
from app.services.purchasing import (
    receive_purchase_order_items as receive_purchase_order_items_service,
)
from app.services.purchasing import (
    reject_purchase_invoice as reject_purchase_invoice_service,
)
from app.services.purchasing import (
    submit_purchase_invoice_for_review as submit_purchase_invoice_for_review_service,
)

router = APIRouter(dependencies=[Depends(require_permissions("purchasing:manage"))])


@router.get("/suppliers", response_model=List[SupplierSchema])
def get_suppliers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(Supplier).order_by(Supplier.id.desc())
    if active_only:
        query = query.filter(Supplier.is_active == True)  # noqa: E712
    return query.offset(skip).limit(limit).all()


@router.post("/suppliers", response_model=SupplierSchema)
def create_supplier(
    supplier_in: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    supplier = Supplier(**supplier_in.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.put("/suppliers/{supplier_id}", response_model=SupplierSchema)
def update_supplier(
    supplier_id: int,
    supplier_in: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    update_data = supplier_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/invoices", response_model=List[PurchaseInvoiceSchema])
def get_purchase_invoices(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None, ge=1),
    purchase_order_id: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(get_current_active_user),
):
    query = (
        db.query(PurchaseInvoice)
        .options(joinedload(PurchaseInvoice.items))
        .order_by(PurchaseInvoice.id.desc())
    )
    if not current_user.is_superuser:
        query = query.filter(PurchaseInvoice.user_id == current_user.id)
    if status:
        query = query.filter(PurchaseInvoice.status == status)
    if supplier_id:
        query = query.filter(PurchaseInvoice.supplier_id == supplier_id)
    if purchase_order_id:
        query = query.filter(PurchaseInvoice.purchase_order_id == purchase_order_id)
    return query.offset(skip).limit(limit).all()


@router.get("/invoices/{invoice_id}", response_model=PurchaseInvoiceSchema)
def get_purchase_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return _get_purchase_invoice_for_user(
        db=db,
        invoice_id=invoice_id,
        current_user=current_user,
    )


@router.post("/invoices", response_model=PurchaseInvoiceSchema)
def create_purchase_invoice(
    invoice_in: PurchaseInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return create_purchase_invoice_service(
        db=db, current_user=current_user, invoice_in=invoice_in
    )


@router.post(
    "/invoices/{invoice_id}/submit-review", response_model=PurchaseInvoiceSchema
)
def submit_purchase_invoice_for_review(
    invoice_id: int,
    action_in: PurchaseInvoiceReviewAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return submit_purchase_invoice_for_review_service(
        db=db, current_user=current_user, invoice_id=invoice_id, action_in=action_in
    )


@router.post("/invoices/{invoice_id}/approve", response_model=PurchaseInvoiceSchema)
def approve_purchase_invoice(
    invoice_id: int,
    action_in: PurchaseInvoiceReviewAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not has_permission(
        db=db, user=current_user, permission_code="purchasing:approve"
    ):
        raise HTTPException(
            status_code=403,
            detail="Missing permission: purchasing:approve",
        )

    return approve_purchase_invoice_service(
        db=db, current_user=current_user, invoice_id=invoice_id, action_in=action_in
    )


@router.post("/invoices/{invoice_id}/reject", response_model=PurchaseInvoiceSchema)
def reject_purchase_invoice(
    invoice_id: int,
    action_in: PurchaseInvoiceReviewAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not has_permission(
        db=db, user=current_user, permission_code="purchasing:approve"
    ):
        raise HTTPException(
            status_code=403,
            detail="Missing permission: purchasing:approve",
        )

    return reject_purchase_invoice_service(
        db=db, current_user=current_user, invoice_id=invoice_id, action_in=action_in
    )


@router.get("/orders", response_model=List[PurchaseOrderSchema])
def get_purchase_orders(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(get_current_active_user),
):
    query = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .order_by(PurchaseOrder.id.desc())
    )
    if not current_user.is_superuser:
        query = query.filter(PurchaseOrder.user_id == current_user.id)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    return query.offset(skip).limit(limit).all()


@router.get("/orders/{purchase_order_id}", response_model=PurchaseOrderSchema)
def get_purchase_order(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    purchase_order = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(PurchaseOrder.id == purchase_order_id)
        .first()
    )
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if not current_user.is_superuser and purchase_order.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this purchase order"
        )
    return purchase_order


@router.post("/orders", response_model=PurchaseOrderSchema)
def create_purchase_order(
    purchase_order_in: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return create_purchase_order_service(
        db=db, current_user=current_user, purchase_order_in=purchase_order_in
    )


@router.post("/orders/from-replenishment", response_model=PurchaseOrderSchema)
def create_purchase_order_from_replenishment(
    payload: PurchaseOrderFromSuggestionsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return create_purchase_order_from_replenishment_service(
        db=db, current_user=current_user, payload=payload
    )


@router.post(
    "/orders/{purchase_order_id}/mark-ordered", response_model=PurchaseOrderSchema
)
def mark_purchase_order_ordered(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return mark_purchase_order_ordered_service(
        db=db, current_user=current_user, purchase_order_id=purchase_order_id
    )


@router.post("/orders/{purchase_order_id}/cancel", response_model=PurchaseOrderSchema)
def cancel_purchase_order(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return cancel_purchase_order_service(
        db=db, current_user=current_user, purchase_order_id=purchase_order_id
    )


@router.post("/orders/{purchase_order_id}/receive", response_model=PurchaseOrderSchema)
def receive_purchase_order_items(
    purchase_order_id: int,
    receive_in: PurchaseOrderReceive,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return receive_purchase_order_items_service(
        db=db,
        current_user=current_user,
        purchase_order_id=purchase_order_id,
        receive_in=receive_in,
    )
