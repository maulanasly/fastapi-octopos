from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import (
    get_current_active_user,
    has_permission,
    require_permissions,
)
from app.core.audit import log_action
from app.core.database import get_db
from app.models.purchase import (
    PurchaseInvoice,
    PurchaseOrder,
    Supplier,
    SupplierPayment,
)
from app.models.user import User
from app.schemas.purchase import PurchaseInvoice as PurchaseInvoiceSchema
from app.schemas.purchase import (
    PurchaseInvoiceCreate,
    PurchaseInvoiceReviewAction,
    PurchaseOrderCreate,
    PurchaseOrderReceive,
    PurchaseOrderReviewAction,
    SupplierCreate,
    SupplierPaymentCreate,
    SupplierPaymentReviewAction,
    SupplierUpdate,
)
from app.schemas.purchase import PurchaseOrder as PurchaseOrderSchema
from app.schemas.purchase import PurchaseOrderDetail as PurchaseOrderDetailSchema
from app.schemas.purchase import Supplier as SupplierSchema
from app.schemas.purchase import SupplierLedger as SupplierLedgerSchema
from app.schemas.purchase import SupplierPayment as SupplierPaymentSchema
from app.schemas.purchasing_setting import (
    PurchasingSettingRead,
    PurchasingSettingUpdate,
)
from app.schemas.replenishment import (
    PurchaseOrderBatchFromSuggestionsCreate,
    PurchaseOrderBatchFromSuggestionsResponse,
    PurchaseOrderFromSuggestionsCreate,
)
from app.services.purchasing import (
    _attach_outstanding_amounts,
    _get_purchase_invoice_for_user,
    get_or_create_purchasing_setting,
    get_purchase_order_detail_data,
    get_supplier_ledger_data,
    update_purchasing_setting,
)
from app.services.purchasing import (
    approve_purchase_invoice as approve_purchase_invoice_service,
)
from app.services.purchasing import (
    approve_supplier_payment as approve_supplier_payment_service,
)
from app.services.purchasing import (
    batch_generate_purchase_orders_from_replenishment as batch_generate_purchase_orders_from_replenishment_service,
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
    create_supplier_payment as create_supplier_payment_service,
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
    reject_purchase_order as reject_purchase_order_service,
)
from app.services.purchasing import (
    reject_supplier_payment as reject_supplier_payment_service,
)
from app.services.purchasing import (
    submit_purchase_invoice_for_review as submit_purchase_invoice_for_review_service,
)
from app.services.purchasing import (
    submit_purchase_order_for_review as submit_purchase_order_for_review_service,
)
from app.services.purchasing import (
    submit_supplier_payment_for_review as submit_supplier_payment_for_review_service,
)

router = APIRouter(dependencies=[Depends(require_permissions("purchasing:manage"))])


def _is_approver(db: Session, current_user: User) -> bool:
    return current_user.is_superuser or has_permission(
        db=db, user=current_user, permission_code="purchasing:approve"
    )


@router.get("/suppliers", response_model=list[SupplierSchema])
def get_suppliers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
):
    query = (
        db.query(Supplier)
        .filter(Supplier.tenant_id == current_user.tenant_id)
        .order_by(Supplier.id.desc())
    )
    if active_only:
        query = query.filter(Supplier.is_active == True)  # noqa: E712
    return query.offset(skip).limit(limit).all()


@router.post("/suppliers", response_model=SupplierSchema)
def create_supplier(
    supplier_in: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    supplier = Supplier(**supplier_in.model_dump(), tenant_id=current_user.tenant_id)
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
    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == supplier_id,
            Supplier.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    update_data = supplier_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/invoices", response_model=list[PurchaseInvoiceSchema])
def get_purchase_invoices(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: str | None = Query(None),
    supplier_id: int | None = Query(None, ge=1),
    purchase_order_id: int | None = Query(None, ge=1),
    current_user: User = Depends(get_current_active_user),
):
    query = (
        db.query(PurchaseInvoice)
        .options(joinedload(PurchaseInvoice.items))
        .filter(PurchaseInvoice.tenant_id == current_user.tenant_id)
        .order_by(PurchaseInvoice.id.desc())
    )
    if not _is_approver(db, current_user):
        query = query.filter(PurchaseInvoice.user_id == current_user.id)
    if status:
        query = query.filter(PurchaseInvoice.status == status)
    if supplier_id:
        query = query.filter(PurchaseInvoice.supplier_id == supplier_id)
    if purchase_order_id:
        query = query.filter(PurchaseInvoice.purchase_order_id == purchase_order_id)
    invoices = query.offset(skip).limit(limit).all()
    _attach_outstanding_amounts(db, invoices, current_user.tenant_id)
    return invoices


@router.get("/invoices/{invoice_id}", response_model=PurchaseInvoiceSchema)
def get_purchase_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    invoice = _get_purchase_invoice_for_user(
        db=db,
        invoice_id=invoice_id,
        current_user=current_user,
        tenant_id=current_user.tenant_id,
    )
    _attach_outstanding_amounts(db, [invoice], current_user.tenant_id)
    return invoice


@router.post("/invoices", response_model=PurchaseInvoiceSchema)
def create_purchase_invoice(
    invoice_in: PurchaseInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    invoice = create_purchase_invoice_service(
        db=db,
        current_user=current_user,
        invoice_in=invoice_in,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="purchase_invoice.create",
        user_id=current_user.id,
        resource_type="purchase_invoice",
        resource_id=invoice.id,
        details={
            "invoice_number": invoice.invoice_number,
            "purchase_order_id": invoice.purchase_order_id,
            "total_amount": float(invoice.total_amount),
        },
    )
    db.commit()
    return invoice


@router.post(
    "/invoices/{invoice_id}/submit-review", response_model=PurchaseInvoiceSchema
)
def submit_purchase_invoice_for_review(
    invoice_id: int,
    action_in: PurchaseInvoiceReviewAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    invoice = submit_purchase_invoice_for_review_service(
        db=db,
        current_user=current_user,
        invoice_id=invoice_id,
        action_in=action_in,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="purchase_invoice.submit",
        user_id=current_user.id,
        resource_type="purchase_invoice",
        resource_id=invoice.id,
        details={"invoice_number": invoice.invoice_number},
    )
    db.commit()
    return invoice


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

    invoice = approve_purchase_invoice_service(
        db=db,
        current_user=current_user,
        invoice_id=invoice_id,
        action_in=action_in,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="purchase_invoice.approve",
        user_id=current_user.id,
        resource_type="purchase_invoice",
        resource_id=invoice.id,
        details={
            "invoice_number": invoice.invoice_number,
            "review_note": invoice.review_note,
        },
    )
    db.commit()
    return invoice


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

    invoice = reject_purchase_invoice_service(
        db=db,
        current_user=current_user,
        invoice_id=invoice_id,
        action_in=action_in,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="purchase_invoice.reject",
        user_id=current_user.id,
        resource_type="purchase_invoice",
        resource_id=invoice.id,
        details={
            "invoice_number": invoice.invoice_number,
            "review_note": invoice.review_note,
        },
    )
    db.commit()
    return invoice


@router.get("/orders", response_model=list[PurchaseOrderSchema])
def get_purchase_orders(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: str | None = Query(None),
    supplier_id: int | None = Query(None, ge=1),
    current_user: User = Depends(get_current_active_user),
):
    query = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(PurchaseOrder.tenant_id == current_user.tenant_id)
        .order_by(PurchaseOrder.id.desc())
    )
    if not _is_approver(db, current_user):
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
        .filter(
            PurchaseOrder.id == purchase_order_id,
            PurchaseOrder.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if not current_user.is_superuser and purchase_order.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this purchase order"
        )
    return purchase_order


@router.get(
    "/orders/{purchase_order_id}/detail", response_model=PurchaseOrderDetailSchema
)
def get_purchase_order_detail(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    purchase_order = (
        db.query(PurchaseOrder)
        .filter(
            PurchaseOrder.id == purchase_order_id,
            PurchaseOrder.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if not _is_approver(db, current_user) and purchase_order.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this purchase order"
        )
    return get_purchase_order_detail_data(
        db=db,
        tenant_id=current_user.tenant_id,
        purchase_order_id=purchase_order_id,
    )


@router.get("/suppliers/{supplier_id}/ledger", response_model=SupplierLedgerSchema)
def get_supplier_ledger(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_supplier_ledger_data(
        db=db,
        tenant_id=current_user.tenant_id,
        supplier_id=supplier_id,
    )


@router.get("/settings", response_model=PurchasingSettingRead)
def get_purchasing_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_or_create_purchasing_setting(db, current_user.tenant_id)


@router.put("/settings", response_model=PurchasingSettingRead)
def update_purchasing_settings(
    settings_in: PurchasingSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return update_purchasing_setting(
        db=db,
        tenant_id=current_user.tenant_id,
        data=settings_in,
    )


@router.post("/orders", response_model=PurchaseOrderSchema)
def create_purchase_order(
    purchase_order_in: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    purchase_order = create_purchase_order_service(
        db=db,
        current_user=current_user,
        purchase_order_in=purchase_order_in,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="purchase_order.create",
        user_id=current_user.id,
        resource_type="purchase_order",
        resource_id=purchase_order.id,
        details={
            "supplier_id": purchase_order.supplier_id,
            "total_estimated_amount": float(purchase_order.total_estimated_amount),
        },
    )
    db.commit()
    return purchase_order


@router.post("/orders/from-replenishment", response_model=PurchaseOrderSchema)
def create_purchase_order_from_replenishment(
    payload: PurchaseOrderFromSuggestionsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    purchase_order = create_purchase_order_from_replenishment_service(
        db=db,
        current_user=current_user,
        payload=payload,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="purchase_order.create",
        user_id=current_user.id,
        resource_type="purchase_order",
        resource_id=purchase_order.id,
        details={
            "supplier_id": purchase_order.supplier_id,
            "total_estimated_amount": float(purchase_order.total_estimated_amount),
            "source": "replenishment",
        },
    )
    db.commit()
    return purchase_order


@router.post(
    "/orders/batch-from-replenishment",
    response_model=PurchaseOrderBatchFromSuggestionsResponse,
)
def batch_generate_purchase_orders_from_replenishment(
    payload: PurchaseOrderBatchFromSuggestionsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = batch_generate_purchase_orders_from_replenishment_service(
        db=db,
        current_user=current_user,
        payload=payload,
        tenant_id=current_user.tenant_id,
    )
    for purchase_order in result["purchase_orders"]:
        log_action(
            db=db,
            action="purchase_order.create",
            user_id=current_user.id,
            resource_type="purchase_order",
            resource_id=purchase_order.id,
            details={
                "supplier_id": purchase_order.supplier_id,
                "total_estimated_amount": float(purchase_order.total_estimated_amount),
                "source": "replenishment_batch",
            },
        )
    db.commit()
    return result


@router.post(
    "/orders/{purchase_order_id}/submit-review", response_model=PurchaseOrderSchema
)
def submit_purchase_order_for_review(
    purchase_order_id: int,
    action_in: PurchaseOrderReviewAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    purchase_order = submit_purchase_order_for_review_service(
        db=db,
        current_user=current_user,
        purchase_order_id=purchase_order_id,
        action_in=action_in,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="purchase_order.submit",
        user_id=current_user.id,
        resource_type="purchase_order",
        resource_id=purchase_order.id,
    )
    db.commit()
    return purchase_order


@router.post(
    "/orders/{purchase_order_id}/mark-ordered", response_model=PurchaseOrderSchema
)
def mark_purchase_order_ordered(
    purchase_order_id: int,
    action_in: PurchaseOrderReviewAction | None = None,
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

    purchase_order = mark_purchase_order_ordered_service(
        db=db,
        current_user=current_user,
        purchase_order_id=purchase_order_id,
        action_in=action_in or PurchaseOrderReviewAction(),
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="purchase_order.approve",
        user_id=current_user.id,
        resource_type="purchase_order",
        resource_id=purchase_order.id,
        details={"review_note": purchase_order.review_note},
    )
    db.commit()
    return purchase_order


@router.post("/orders/{purchase_order_id}/reject", response_model=PurchaseOrderSchema)
def reject_purchase_order(
    purchase_order_id: int,
    action_in: PurchaseOrderReviewAction,
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

    purchase_order = reject_purchase_order_service(
        db=db,
        current_user=current_user,
        purchase_order_id=purchase_order_id,
        action_in=action_in,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="purchase_order.reject",
        user_id=current_user.id,
        resource_type="purchase_order",
        resource_id=purchase_order.id,
        details={"review_note": purchase_order.review_note},
    )
    db.commit()
    return purchase_order


@router.post("/orders/{purchase_order_id}/cancel", response_model=PurchaseOrderSchema)
def cancel_purchase_order(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    purchase_order = cancel_purchase_order_service(
        db=db,
        current_user=current_user,
        purchase_order_id=purchase_order_id,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="purchase_order.cancel",
        user_id=current_user.id,
        resource_type="purchase_order",
        resource_id=purchase_order.id,
    )
    db.commit()
    return purchase_order


@router.post("/orders/{purchase_order_id}/receive", response_model=PurchaseOrderSchema)
def receive_purchase_order_items(
    purchase_order_id: int,
    receive_in: PurchaseOrderReceive,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    purchase_order = receive_purchase_order_items_service(
        db=db,
        current_user=current_user,
        purchase_order_id=purchase_order_id,
        receive_in=receive_in,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="purchase_order.receive",
        user_id=current_user.id,
        resource_type="purchase_order",
        resource_id=purchase_order.id,
        details={
            "received_items": [
                {
                    "purchase_order_item_id": item.purchase_order_item_id,
                    "quantity_received": item.quantity_received,
                }
                for item in receive_in.items
            ]
        },
    )
    db.commit()
    return purchase_order


# ------------------------------------------------------------- supplier payments


@router.get("/payments", response_model=list[SupplierPaymentSchema])
def get_supplier_payments(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: str | None = Query(None),
    supplier_id: int | None = Query(None, ge=1),
    invoice_id: int | None = Query(None, ge=1),
    current_user: User = Depends(get_current_active_user),
):
    query = (
        db.query(SupplierPayment)
        .filter(SupplierPayment.tenant_id == current_user.tenant_id)
        .order_by(SupplierPayment.id.desc())
    )
    if not _is_approver(db, current_user):
        query = query.filter(SupplierPayment.user_id == current_user.id)
    if status:
        query = query.filter(SupplierPayment.status == status)
    if supplier_id:
        query = query.filter(SupplierPayment.supplier_id == supplier_id)
    if invoice_id:
        query = query.filter(SupplierPayment.invoice_id == invoice_id)
    return query.offset(skip).limit(limit).all()


@router.post("/payments", response_model=SupplierPaymentSchema)
def create_supplier_payment(
    payment_in: SupplierPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    payment = create_supplier_payment_service(
        db=db,
        current_user=current_user,
        payment_in=payment_in,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="supplier_payment.create",
        user_id=current_user.id,
        resource_type="supplier_payment",
        resource_id=payment.id,
        details={
            "invoice_id": payment.invoice_id,
            "amount": float(payment.amount),
            "payment_method": payment.payment_method,
        },
    )
    db.commit()
    return payment


@router.post(
    "/payments/{payment_id}/submit-review", response_model=SupplierPaymentSchema
)
def submit_supplier_payment_for_review(
    payment_id: int,
    action_in: SupplierPaymentReviewAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    payment = submit_supplier_payment_for_review_service(
        db=db,
        current_user=current_user,
        payment_id=payment_id,
        action_in=action_in,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="supplier_payment.submit",
        user_id=current_user.id,
        resource_type="supplier_payment",
        resource_id=payment.id,
        details={"amount": float(payment.amount)},
    )
    db.commit()
    return payment


@router.post("/payments/{payment_id}/approve", response_model=SupplierPaymentSchema)
def approve_supplier_payment(
    payment_id: int,
    action_in: SupplierPaymentReviewAction,
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

    payment = approve_supplier_payment_service(
        db=db,
        current_user=current_user,
        payment_id=payment_id,
        action_in=action_in,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="supplier_payment.approve",
        user_id=current_user.id,
        resource_type="supplier_payment",
        resource_id=payment.id,
        details={
            "invoice_id": payment.invoice_id,
            "amount": float(payment.amount),
            "review_note": payment.review_note,
        },
    )
    db.commit()
    return payment


@router.post("/payments/{payment_id}/reject", response_model=SupplierPaymentSchema)
def reject_supplier_payment(
    payment_id: int,
    action_in: SupplierPaymentReviewAction,
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

    payment = reject_supplier_payment_service(
        db=db,
        current_user=current_user,
        payment_id=payment_id,
        action_in=action_in,
        tenant_id=current_user.tenant_id,
    )
    log_action(
        db=db,
        action="supplier_payment.reject",
        user_id=current_user.id,
        resource_type="supplier_payment",
        resource_id=payment.id,
        details={
            "amount": float(payment.amount),
            "review_note": payment.review_note,
        },
    )
    db.commit()
    return payment
