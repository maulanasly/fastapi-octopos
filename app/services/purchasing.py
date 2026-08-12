from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.money import money_to_float
from app.core.replenishment import build_replenishment_suggestions
from app.models.product import Product
from app.models.purchase import (
    PurchaseInvoice,
    PurchaseInvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.purchase import (
    PurchaseInvoiceCreate,
    PurchaseInvoiceReviewAction,
    PurchaseOrderCreate,
    PurchaseOrderReceive,
)
from app.schemas.replenishment import PurchaseOrderFromSuggestionsCreate


def _get_purchase_invoice_for_user(
    db: Session,
    invoice_id: int,
    current_user: User,
) -> PurchaseInvoice:
    invoice = (
        db.query(PurchaseInvoice)
        .options(joinedload(PurchaseInvoice.items))
        .filter(PurchaseInvoice.id == invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Purchase invoice not found")
    if not current_user.is_superuser and invoice.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this purchase invoice"
        )
    return invoice


def create_purchase_invoice(
    db: Session,
    current_user: User,
    invoice_in: PurchaseInvoiceCreate,
) -> PurchaseInvoice:
    if not invoice_in.items:
        raise HTTPException(
            status_code=400, detail="Invoice must contain at least one item"
        )

    purchase_order = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(PurchaseOrder.id == invoice_in.purchase_order_id)
        .first()
    )
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if not current_user.is_superuser and purchase_order.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to invoice this purchase order"
        )
    if purchase_order.status == "cancelled":
        raise HTTPException(
            status_code=400, detail="Cannot create invoice for cancelled purchase order"
        )

    normalized_invoice_number = invoice_in.invoice_number.strip()
    if not normalized_invoice_number:
        raise HTTPException(status_code=400, detail="Invoice number cannot be empty")

    duplicate_invoice = (
        db.query(PurchaseInvoice)
        .filter(
            PurchaseInvoice.supplier_id == purchase_order.supplier_id,
            PurchaseInvoice.invoice_number == normalized_invoice_number,
        )
        .first()
    )
    if duplicate_invoice:
        raise HTTPException(
            status_code=400,
            detail="Invoice number already exists for this supplier",
        )

    po_item_map = {item.id: item for item in purchase_order.items}
    billed_item_ids = [item.purchase_order_item_id for item in invoice_in.items]
    if len(billed_item_ids) != len(set(billed_item_ids)):
        raise HTTPException(
            status_code=400,
            detail="Duplicate purchase_order_item_id in invoice items is not allowed",
        )

    existing_billed_rows = (
        db.query(
            PurchaseInvoiceItem.purchase_order_item_id,
            func.coalesce(func.sum(PurchaseInvoiceItem.billed_quantity), 0),
        )
        .join(PurchaseInvoice, PurchaseInvoiceItem.invoice_id == PurchaseInvoice.id)
        .filter(
            PurchaseInvoice.purchase_order_id == purchase_order.id,
            PurchaseInvoice.status != "rejected",
        )
        .group_by(PurchaseInvoiceItem.purchase_order_item_id)
        .all()
    )
    existing_billed_map = {row[0]: int(row[1] or 0) for row in existing_billed_rows}

    invoice_items: List[PurchaseInvoiceItem] = []
    subtotal_amount = 0.0
    variance_amount = 0.0
    has_quantity_variance = False
    has_price_variance = False

    for billed_item in invoice_in.items:
        po_item = po_item_map.get(billed_item.purchase_order_item_id)
        if not po_item:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Purchase order item {billed_item.purchase_order_item_id} "
                    "not found in this purchase order"
                ),
            )

        previously_billed_quantity = existing_billed_map.get(po_item.id, 0)
        expected_quantity = max(
            po_item.quantity_received - previously_billed_quantity, 0
        )
        billed_quantity = billed_item.billed_quantity
        billed_unit_cost = billed_item.billed_unit_cost
        expected_unit_cost = money_to_float(po_item.unit_cost)

        cumulative_billed_quantity = previously_billed_quantity + billed_quantity
        quantity_variance = billed_quantity - expected_quantity
        price_variance = billed_unit_cost - expected_unit_cost
        line_total = billed_quantity * billed_unit_cost
        expected_line_total = expected_quantity * expected_unit_cost
        line_variance_amount = line_total - expected_line_total

        if any(
            (
                quantity_variance != 0,
                cumulative_billed_quantity > po_item.quantity_received,
                cumulative_billed_quantity > po_item.quantity_ordered,
            )
        ):
            has_quantity_variance = True

        if abs(price_variance) > 1e-9:
            has_price_variance = True

        subtotal_amount += line_total
        variance_amount += line_variance_amount

        invoice_items.append(
            PurchaseInvoiceItem(
                purchase_order_item_id=po_item.id,
                product_id=po_item.product_id,
                billed_quantity=billed_quantity,
                billed_unit_cost=billed_unit_cost,
                expected_quantity=expected_quantity,
                expected_unit_cost=expected_unit_cost,
                quantity_variance=quantity_variance,
                price_variance=price_variance,
                line_total=line_total,
            )
        )

    purchase_invoice = PurchaseInvoice(
        supplier_id=purchase_order.supplier_id,
        purchase_order_id=purchase_order.id,
        user_id=current_user.id,
        invoice_number=normalized_invoice_number,
        status="draft",
        invoice_date=invoice_in.invoice_date,
        due_date=invoice_in.due_date,
        subtotal_amount=subtotal_amount,
        total_amount=subtotal_amount,
        variance_amount=variance_amount,
        has_quantity_variance=has_quantity_variance,
        has_price_variance=has_price_variance,
        notes=invoice_in.notes,
    )
    db.add(purchase_invoice)
    db.flush()

    for invoice_item in invoice_items:
        invoice_item.invoice_id = purchase_invoice.id
        db.add(invoice_item)

    db.commit()
    return (
        db.query(PurchaseInvoice)
        .options(joinedload(PurchaseInvoice.items))
        .filter(PurchaseInvoice.id == purchase_invoice.id)
        .first()
    )


def submit_purchase_invoice_for_review(
    db: Session,
    current_user: User,
    invoice_id: int,
    action_in: PurchaseInvoiceReviewAction,
) -> PurchaseInvoice:
    invoice = _get_purchase_invoice_for_user(
        db=db,
        invoice_id=invoice_id,
        current_user=current_user,
    )
    if invoice.status != "draft":
        raise HTTPException(
            status_code=400, detail="Only draft invoices can be submitted for review"
        )

    invoice.status = "pending_review"
    invoice.review_note = action_in.review_note
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def approve_purchase_invoice(
    db: Session,
    current_user: User,
    invoice_id: int,
    action_in: PurchaseInvoiceReviewAction,
) -> PurchaseInvoice:
    invoice = _get_purchase_invoice_for_user(
        db=db,
        invoice_id=invoice_id,
        current_user=current_user,
    )
    if invoice.status != "pending_review":
        raise HTTPException(
            status_code=400, detail="Only pending_review invoices can be approved"
        )

    invoice.status = "approved"
    invoice.review_note = action_in.review_note
    invoice.approved_at = datetime.now(timezone.utc)
    invoice.rejected_at = None
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def reject_purchase_invoice(
    db: Session,
    current_user: User,
    invoice_id: int,
    action_in: PurchaseInvoiceReviewAction,
) -> PurchaseInvoice:
    invoice = _get_purchase_invoice_for_user(
        db=db,
        invoice_id=invoice_id,
        current_user=current_user,
    )
    if invoice.status != "pending_review":
        raise HTTPException(
            status_code=400, detail="Only pending_review invoices can be rejected"
        )

    invoice.status = "rejected"
    invoice.review_note = action_in.review_note
    invoice.rejected_at = datetime.now(timezone.utc)
    invoice.approved_at = None
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def create_purchase_order(
    db: Session,
    current_user: User,
    purchase_order_in: PurchaseOrderCreate,
) -> PurchaseOrder:
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


def create_purchase_order_from_replenishment(
    db: Session,
    current_user: User,
    payload: PurchaseOrderFromSuggestionsCreate,
) -> PurchaseOrder:
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


def mark_purchase_order_ordered(
    db: Session,
    current_user: User,
    purchase_order_id: int,
) -> PurchaseOrder:
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


def cancel_purchase_order(
    db: Session,
    current_user: User,
    purchase_order_id: int,
) -> PurchaseOrder:
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


def receive_purchase_order_items(
    db: Session,
    current_user: User,
    purchase_order_id: int,
    receive_in: PurchaseOrderReceive,
) -> PurchaseOrder:
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
