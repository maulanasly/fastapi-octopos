from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.core.replenishment import build_replenishment_suggestions
from app.models.product import Product
from app.models.purchase import PurchaseOrder, PurchaseOrderItem, Supplier
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.purchase import PurchaseOrder as PurchaseOrderSchema
from app.schemas.purchase import PurchaseOrderCreate, PurchaseOrderReceive
from app.schemas.purchase import Supplier as SupplierSchema
from app.schemas.purchase import SupplierCreate, SupplierUpdate
from app.schemas.replenishment import PurchaseOrderFromSuggestionsCreate

router = APIRouter()


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
    if not purchase_order_in.items:
        raise HTTPException(
            status_code=400, detail="Purchase order must contain at least one item"
        )

    supplier = (
        db.query(Supplier).filter(Supplier.id == purchase_order_in.supplier_id).first()
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if not supplier.is_active:
        raise HTTPException(status_code=400, detail="Supplier is inactive")

    product_ids = [item.product_id for item in purchase_order_in.items]
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    product_map = {product.id: product for product in products}
    missing_product_ids = [pid for pid in product_ids if pid not in product_map]
    if missing_product_ids:
        missing_products_text = ", ".join(
            str(product_id) for product_id in sorted(missing_product_ids)
        )
        raise HTTPException(
            status_code=404,
            detail=f"Product(s) not found: {missing_products_text}",
        )

    total_estimated_amount = sum(
        item.quantity_ordered * item.unit_cost for item in purchase_order_in.items
    )

    purchase_order = PurchaseOrder(
        supplier_id=purchase_order_in.supplier_id,
        user_id=current_user.id,
        status="draft",
        total_estimated_amount=total_estimated_amount,
        notes=purchase_order_in.notes,
    )
    db.add(purchase_order)
    db.flush()

    for item in purchase_order_in.items:
        db.add(
            PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                product_id=item.product_id,
                quantity_ordered=item.quantity_ordered,
                quantity_received=0,
                unit_cost=item.unit_cost,
            )
        )

    db.commit()
    return (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(PurchaseOrder.id == purchase_order.id)
        .first()
    )


@router.post("/orders/from-replenishment", response_model=PurchaseOrderSchema)
def create_purchase_order_from_replenishment(
    payload: PurchaseOrderFromSuggestionsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    supplier = db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if not supplier.is_active:
        raise HTTPException(status_code=400, detail="Supplier is inactive")

    product_query = db.query(Product).order_by(Product.id.asc())
    requested_product_ids = payload.product_ids or []
    if requested_product_ids:
        unique_product_ids = sorted(set(requested_product_ids))
        product_query = product_query.filter(Product.id.in_(unique_product_ids))
    else:
        unique_product_ids = []

    products = product_query.all()
    product_map = {product.id: product for product in products}
    missing_product_ids = [
        product_id for product_id in unique_product_ids if product_id not in product_map
    ]
    if missing_product_ids:
        missing_products_text = ", ".join(
            str(product_id) for product_id in missing_product_ids
        )
        raise HTTPException(
            status_code=404,
            detail=f"Product(s) not found: {missing_products_text}",
        )

    suggestions = build_replenishment_suggestions(
        db=db,
        products=products,
        lookback_days=payload.lookback_days,
    )
    if payload.include_only_reorder:
        suggestions = [item for item in suggestions if item.should_reorder]

    suggestion_items = [
        item for item in suggestions if item.recommended_order_quantity > 0
    ]
    if not suggestion_items:
        raise HTTPException(
            status_code=400,
            detail="No replenishment suggestions with recommended quantity > 0",
        )

    total_estimated_amount = sum(
        item.recommended_order_quantity * product_map[item.product_id].price
        for item in suggestion_items
    )

    notes = payload.notes or (
        "Auto-generated from replenishment suggestions "
        f"(lookback_days={payload.lookback_days})"
    )
    purchase_order = PurchaseOrder(
        supplier_id=supplier.id,
        user_id=current_user.id,
        status="draft",
        total_estimated_amount=total_estimated_amount,
        notes=notes,
    )
    db.add(purchase_order)
    db.flush()

    for suggestion in suggestion_items:
        product = product_map[suggestion.product_id]
        db.add(
            PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                product_id=product.id,
                quantity_ordered=suggestion.recommended_order_quantity,
                quantity_received=0,
                unit_cost=product.price,
            )
        )

    db.commit()
    return (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(PurchaseOrder.id == purchase_order.id)
        .first()
    )


@router.post(
    "/orders/{purchase_order_id}/mark-ordered", response_model=PurchaseOrderSchema
)
def mark_purchase_order_ordered(
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
            status_code=403, detail="Not authorized to update this purchase order"
        )
    if purchase_order.status != "draft":
        raise HTTPException(
            status_code=400, detail="Only draft purchase orders can be marked ordered"
        )

    purchase_order.status = "ordered"
    purchase_order.ordered_at = datetime.now(timezone.utc)
    db.add(purchase_order)
    db.commit()
    db.refresh(purchase_order)
    return purchase_order


@router.post("/orders/{purchase_order_id}/cancel", response_model=PurchaseOrderSchema)
def cancel_purchase_order(
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
            status_code=403, detail="Not authorized to cancel this purchase order"
        )
    if purchase_order.status == "cancelled":
        raise HTTPException(
            status_code=400, detail="Purchase order is already cancelled"
        )
    if any(item.quantity_received > 0 for item in purchase_order.items):
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel purchase order that has received items",
        )

    purchase_order.status = "cancelled"
    db.add(purchase_order)
    db.commit()
    db.refresh(purchase_order)
    return purchase_order


@router.post("/orders/{purchase_order_id}/receive", response_model=PurchaseOrderSchema)
def receive_purchase_order_items(
    purchase_order_id: int,
    receive_in: PurchaseOrderReceive,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not receive_in.items:
        raise HTTPException(
            status_code=400, detail="Receive request must contain at least one item"
        )

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
            status_code=403, detail="Not authorized to receive this purchase order"
        )
    if purchase_order.status in ("cancelled", "received"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot receive items for a {purchase_order.status} purchase order",
        )

    po_item_map = {item.id: item for item in purchase_order.items}
    receipt_quantities = {}
    for item in receive_in.items:
        current_qty = receipt_quantities.get(item.purchase_order_item_id, 0)
        receipt_quantities[item.purchase_order_item_id] = (
            current_qty + item.quantity_received
        )

    for po_item_id, quantity_received in receipt_quantities.items():
        po_item = po_item_map.get(po_item_id)
        if not po_item:
            raise HTTPException(
                status_code=400,
                detail=f"Purchase order item {po_item_id} not found in this purchase order",
            )
        remaining_quantity = po_item.quantity_ordered - po_item.quantity_received
        if quantity_received > remaining_quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Receive quantity exceeds remaining quantity for purchase order item "
                    f"{po_item_id}. Requested: {quantity_received}, available: {remaining_quantity}"
                ),
            )

    for po_item_id, quantity_received in receipt_quantities.items():
        po_item = po_item_map[po_item_id]
        product = db.query(Product).filter(Product.id == po_item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with id {po_item.product_id} not found",
            )

        quantity_before = product.stock_quantity
        product.stock_quantity += quantity_received
        po_item.quantity_received += quantity_received

        db.add(product)
        db.add(po_item)
        db.add(
            StockMovement(
                product_id=product.id,
                user_id=current_user.id,
                purchase_order_id=purchase_order.id,
                purchase_order_item_id=po_item.id,
                movement_type="purchase_receipt",
                quantity_before=quantity_before,
                quantity_delta=quantity_received,
                quantity_after=product.stock_quantity,
                note="Stock increased by purchase order receipt",
            )
        )

    all_received = all(
        item.quantity_received >= item.quantity_ordered for item in purchase_order.items
    )
    any_received = any(item.quantity_received > 0 for item in purchase_order.items)

    if all_received:
        purchase_order.status = "received"
        purchase_order.received_at = datetime.now(timezone.utc)
    elif any_received:
        purchase_order.status = "partially_received"
    elif purchase_order.status == "draft":
        purchase_order.status = "ordered"

    db.add(purchase_order)
    db.commit()

    return (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(PurchaseOrder.id == purchase_order.id)
        .first()
    )
