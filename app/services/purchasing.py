from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import has_permission
from app.core.money import quantize_money, to_decimal
from app.core.replenishment import build_replenishment_suggestions
from app.models.product import Product
from app.models.purchase import (
    PurchaseInvoice,
    PurchaseInvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
    SupplierPayment,
)
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.purchase import (
    PurchaseInvoiceCreate,
    PurchaseInvoiceReviewAction,
    PurchaseOrderCreate,
    PurchaseOrderReceive,
    PurchaseOrderReviewAction,
    SupplierPaymentCreate,
    SupplierPaymentReviewAction,
)
from app.schemas.replenishment import (
    PurchaseOrderBatchFromSuggestionsCreate,
    PurchaseOrderFromSuggestionsCreate,
)


def _can_access_any_tenant_document(db: Session, current_user: User) -> bool:
    """Approvers (and superusers) see the whole tenant review queue."""
    if current_user.is_superuser:
        return True
    return has_permission(
        db=db, user=current_user, permission_code="purchasing:approve"
    )


def _get_purchase_invoice_for_user(
    db: Session,
    invoice_id: int,
    current_user: User,
    tenant_id: int,
) -> PurchaseInvoice:
    invoice = (
        db.query(PurchaseInvoice)
        .options(joinedload(PurchaseInvoice.items))
        .filter(
            PurchaseInvoice.id == invoice_id,
            PurchaseInvoice.tenant_id == tenant_id,
        )
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Purchase invoice not found")
    if (
        not _can_access_any_tenant_document(db, current_user)
        and invoice.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this purchase invoice"
        )
    return invoice


def create_purchase_invoice(
    db: Session,
    current_user: User,
    invoice_in: PurchaseInvoiceCreate,
    tenant_id: int,
) -> PurchaseInvoice:
    if not invoice_in.items:
        raise HTTPException(
            status_code=400, detail="Invoice must contain at least one item"
        )

    purchase_order = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(
            PurchaseOrder.id == invoice_in.purchase_order_id,
            PurchaseOrder.tenant_id == tenant_id,
        )
        .first()
    )
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if (
        not _can_access_any_tenant_document(db, current_user)
        and purchase_order.user_id != current_user.id
    ):
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
            PurchaseInvoice.tenant_id == tenant_id,
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
            PurchaseInvoice.tenant_id == tenant_id,
        )
        .group_by(PurchaseInvoiceItem.purchase_order_item_id)
        .all()
    )
    existing_billed_map = {row[0]: int(row[1] or 0) for row in existing_billed_rows}

    invoice_items: list[PurchaseInvoiceItem] = []
    subtotal_amount = Decimal("0")
    variance_amount = Decimal("0")
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
        billed_unit_cost = quantize_money(to_decimal(billed_item.billed_unit_cost))
        expected_unit_cost = quantize_money(to_decimal(po_item.unit_cost))

        cumulative_billed_quantity = previously_billed_quantity + billed_quantity
        quantity_variance = billed_quantity - expected_quantity
        price_variance = billed_unit_cost - expected_unit_cost
        line_total = quantize_money(to_decimal(billed_quantity) * billed_unit_cost)
        expected_line_total = quantize_money(
            to_decimal(expected_quantity) * expected_unit_cost
        )
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
                tenant_id=tenant_id,
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
        tenant_id=tenant_id,
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
        .filter(
            PurchaseInvoice.id == purchase_invoice.id,
            PurchaseInvoice.tenant_id == tenant_id,
        )
        .first()
    )


def submit_purchase_invoice_for_review(
    db: Session,
    current_user: User,
    invoice_id: int,
    action_in: PurchaseInvoiceReviewAction,
    tenant_id: int,
) -> PurchaseInvoice:
    invoice = _get_purchase_invoice_for_user(
        db=db,
        invoice_id=invoice_id,
        current_user=current_user,
        tenant_id=tenant_id,
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
    tenant_id: int,
) -> PurchaseInvoice:
    invoice = _get_purchase_invoice_for_user(
        db=db,
        invoice_id=invoice_id,
        current_user=current_user,
        tenant_id=tenant_id,
    )
    if invoice.status != "pending_review":
        raise HTTPException(
            status_code=400, detail="Only pending_review invoices can be approved"
        )
    if not current_user.is_superuser and invoice.user_id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Cannot approve a purchase invoice you created",
        )

    invoice.status = "approved"
    invoice.review_note = action_in.review_note
    invoice.approved_at = datetime.now(UTC)
    invoice.rejected_at = None
    db.add(invoice)

    for item in invoice.items:
        product = (
            db.query(Product)
            .filter(
                Product.id == item.product_id,
                Product.tenant_id == tenant_id,
            )
            .first()
        )
        if product:
            product.unit_cost = item.billed_unit_cost
            db.add(product)

    db.commit()
    db.refresh(invoice)
    return invoice


def reject_purchase_invoice(
    db: Session,
    current_user: User,
    invoice_id: int,
    action_in: PurchaseInvoiceReviewAction,
    tenant_id: int,
) -> PurchaseInvoice:
    invoice = _get_purchase_invoice_for_user(
        db=db,
        invoice_id=invoice_id,
        current_user=current_user,
        tenant_id=tenant_id,
    )
    if invoice.status != "pending_review":
        raise HTTPException(
            status_code=400, detail="Only pending_review invoices can be rejected"
        )

    invoice.status = "rejected"
    invoice.review_note = action_in.review_note
    invoice.rejected_at = datetime.now(UTC)
    invoice.approved_at = None
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def create_purchase_order(
    db: Session,
    current_user: User,
    purchase_order_in: PurchaseOrderCreate,
    tenant_id: int,
) -> PurchaseOrder:
    if not purchase_order_in.items:
        raise HTTPException(
            status_code=400, detail="Purchase order must contain at least one item"
        )

    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == purchase_order_in.supplier_id,
            Supplier.tenant_id == tenant_id,
        )
        .first()
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if not supplier.is_active:
        raise HTTPException(status_code=400, detail="Supplier is inactive")

    product_ids = [item.product_id for item in purchase_order_in.items]
    products = (
        db.query(Product)
        .filter(
            Product.id.in_(product_ids),
            Product.tenant_id == tenant_id,
        )
        .all()
    )
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
        quantize_money(to_decimal(item.quantity_ordered) * to_decimal(item.unit_cost))
        for item in purchase_order_in.items
    )

    purchase_order = PurchaseOrder(
        supplier_id=purchase_order_in.supplier_id,
        user_id=current_user.id,
        tenant_id=tenant_id,
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
                tenant_id=tenant_id,
                quantity_ordered=item.quantity_ordered,
                quantity_received=0,
                unit_cost=item.unit_cost,
            )
        )

    db.commit()
    return (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(
            PurchaseOrder.id == purchase_order.id,
            PurchaseOrder.tenant_id == tenant_id,
        )
        .first()
    )


def _supplier_for_products(db: Session, product_ids: list[int]) -> dict[int, int]:
    """Most recently used supplier per product (by purchase order id)."""
    rows = (
        db.query(PurchaseOrderItem.product_id, PurchaseOrder.supplier_id)
        .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
        .filter(PurchaseOrderItem.product_id.in_(product_ids))
        .order_by(PurchaseOrder.id.desc())
        .all()
    )
    supplier_map: dict[int, int] = {}
    for product_id, supplier_id in rows:
        supplier_map.setdefault(product_id, supplier_id)
    if len(supplier_map) < len(product_ids):
        invoice_rows = (
            db.query(PurchaseInvoiceItem.product_id, PurchaseOrder.supplier_id)
            .join(
                PurchaseOrderItem,
                PurchaseInvoiceItem.purchase_order_item_id == PurchaseOrderItem.id,
            )
            .join(
                PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id
            )
            .filter(
                PurchaseInvoiceItem.product_id.in_(product_ids),
                ~PurchaseInvoiceItem.product_id.in_(list(supplier_map)),
            )
            .order_by(PurchaseOrder.id.desc())
            .all()
        )
        for product_id, supplier_id in invoice_rows:
            supplier_map.setdefault(product_id, supplier_id)

    # Fallback: products with no purchase/invoice history default to the
    # tenant's only active supplier, so a fresh catalog can still be ordered.
    missing_ids = [pid for pid in product_ids if pid not in supplier_map]
    if missing_ids:
        tenant_rows = (
            db.query(Product.id, Product.tenant_id)
            .filter(Product.id.in_(missing_ids))
            .all()
        )
        by_tenant: dict[int, list[int]] = defaultdict(list)
        for product_id, tenant_id in tenant_rows:
            by_tenant[tenant_id].append(product_id)
        for tenant_id, tenant_product_ids in by_tenant.items():
            active_suppliers = (
                db.query(Supplier.id)
                .filter(
                    Supplier.tenant_id == tenant_id,
                    Supplier.is_active.is_(True),
                )
                .all()
            )
            if len(active_suppliers) == 1:
                for product_id in tenant_product_ids:
                    supplier_map[product_id] = active_suppliers[0][0]
    return supplier_map


def supplier_map_with_names(
    db: Session, product_ids: list[int]
) -> dict[int, tuple[int, str]]:
    """Supplier resolution keyed by product, including the supplier name."""
    ids = _supplier_for_products(db, product_ids)
    if not ids:
        return {}
    names = dict(
        db.query(Supplier.id, Supplier.name)
        .filter(Supplier.id.in_(set(ids.values())))
        .all()
    )
    return {
        product_id: (supplier_id, names[supplier_id])
        for product_id, supplier_id in ids.items()
        if supplier_id in names
    }


def _products_already_in_pending_po(db: Session) -> set[int]:
    rows = (
        db.query(PurchaseOrderItem.product_id)
        .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
        .filter(PurchaseOrder.status.in_(("draft", "ordered", "partially_received")))
        .all()
    )
    return {row[0] for row in rows}


def batch_generate_purchase_orders_from_replenishment(
    db: Session,
    current_user: User,
    payload: PurchaseOrderBatchFromSuggestionsCreate,
    tenant_id: int,
) -> dict:
    """Create one draft PO per supplier from replenishment suggestions.

    Honors per-product overrides (quantity, unit cost, supplier) and returns
    every skipped product with the reason it was left out.
    """
    overrides = {
        item.product_id: item for item in (payload.items or []) if item is not None
    }
    requested_ids = payload.product_ids or list(overrides)

    product_query = (
        db.query(Product)
        .filter(Product.tenant_id == tenant_id)
        .order_by(Product.id.asc())
    )
    if requested_ids:
        unique_product_ids = sorted(set(requested_ids))
        product_query = product_query.filter(Product.id.in_(unique_product_ids))
        products = product_query.all()
        missing_product_ids = [
            product_id
            for product_id in unique_product_ids
            if product_id not in {product.id for product in products}
        ]
        if missing_product_ids:
            missing_products_text = ", ".join(
                str(product_id) for product_id in missing_product_ids
            )
            raise HTTPException(
                status_code=404,
                detail=f"Product(s) not found: {missing_products_text}",
            )
    else:
        products = [
            product
            for product in product_query.all()
            if product.stock_quantity <= product.reorder_point
        ]
    if not products:
        return {"purchase_orders": [], "skipped_products": []}

    pending_products = _products_already_in_pending_po(db)
    candidates: list[Product] = []
    skipped: list[dict] = []
    for product in products:
        if product.id in pending_products:
            skipped.append(
                {
                    "product_id": product.id,
                    "reason": "already covered by a pending purchase order",
                }
            )
        else:
            candidates.append(product)
    if not candidates:
        return {"purchase_orders": [], "skipped_products": skipped}

    suggestions = build_replenishment_suggestions(
        db=db,
        products=candidates,
        lookback_days=payload.lookback_days,
        supplier_map=supplier_map_with_names(
            db, [product.id for product in candidates]
        ),
    )

    by_supplier: dict[int, list[dict]] = defaultdict(list)
    for suggestion in suggestions:
        override = overrides.get(suggestion.product_id)
        quantity = (
            override.quantity_ordered
            if override and override.quantity_ordered is not None
            else suggestion.recommended_order_quantity
        )
        if quantity <= 0:
            skipped.append(
                {
                    "product_id": suggestion.product_id,
                    "reason": "no reorder needed",
                }
            )
            continue
        supplier_id = (
            override.supplier_id
            if override and override.supplier_id is not None
            else suggestion.suggested_supplier_id
        )
        if supplier_id is None:
            skipped.append(
                {
                    "product_id": suggestion.product_id,
                    "reason": "no supplier history",
                }
            )
            continue
        unit_cost = (
            override.unit_cost
            if override and override.unit_cost is not None
            else suggestion.unit_cost
        )
        by_supplier[supplier_id].append(
            {
                "product_id": suggestion.product_id,
                "quantity": quantity,
                "unit_cost": unit_cost,
            }
        )

    suppliers_by_id = {
        supplier.id: supplier
        for supplier in db.query(Supplier).filter(Supplier.id.in_(by_supplier)).all()
        if supplier.tenant_id == tenant_id
    }
    for supplier_id in sorted(by_supplier):
        supplier = suppliers_by_id.get(supplier_id)
        if supplier is None:
            skipped.extend(
                {
                    "product_id": spec["product_id"],
                    "reason": "supplier not found",
                }
                for spec in by_supplier.pop(supplier_id)
            )
        elif not supplier.is_active:
            skipped.extend(
                {
                    "product_id": spec["product_id"],
                    "reason": "supplier inactive",
                }
                for spec in by_supplier.pop(supplier_id)
            )

    notes = payload.notes or (
        "Generated from replenishment suggestions "
        f"(lookback_days={payload.lookback_days})"
    )
    created_orders: list[PurchaseOrder] = []
    for supplier_id, specs in by_supplier.items():
        purchase_order = PurchaseOrder(
            supplier_id=supplier_id,
            user_id=current_user.id,
            tenant_id=tenant_id,
            status="draft",
            total_estimated_amount=sum(
                spec["quantity"] * spec["unit_cost"] for spec in specs
            ),
            notes=notes,
        )
        db.add(purchase_order)
        db.flush()
        for spec in specs:
            db.add(
                PurchaseOrderItem(
                    purchase_order_id=purchase_order.id,
                    product_id=spec["product_id"],
                    tenant_id=tenant_id,
                    quantity_ordered=spec["quantity"],
                    quantity_received=0,
                    unit_cost=spec["unit_cost"],
                )
            )
        created_orders.append(purchase_order)
    db.commit()

    created_orders = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(
            PurchaseOrder.id.in_([order.id for order in created_orders]),
            PurchaseOrder.tenant_id == tenant_id,
        )
        .order_by(PurchaseOrder.id.asc())
        .all()
    )
    return {"purchase_orders": created_orders, "skipped_products": skipped}


def create_purchase_order_from_replenishment(
    db: Session,
    current_user: User,
    payload: PurchaseOrderFromSuggestionsCreate,
    tenant_id: int,
) -> PurchaseOrder:
    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == payload.supplier_id,
            Supplier.tenant_id == tenant_id,
        )
        .first()
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if not supplier.is_active:
        raise HTTPException(status_code=400, detail="Supplier is inactive")

    product_query = (
        db.query(Product)
        .filter(Product.tenant_id == tenant_id)
        .order_by(Product.id.asc())
    )
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
        tenant_id=tenant_id,
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
                tenant_id=tenant_id,
                quantity_ordered=suggestion.recommended_order_quantity,
                quantity_received=0,
                unit_cost=product.price,
            )
        )

    db.commit()
    return (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(
            PurchaseOrder.id == purchase_order.id,
            PurchaseOrder.tenant_id == tenant_id,
        )
        .first()
    )


def _get_purchase_order_for_user(
    db: Session,
    current_user: User,
    purchase_order_id: int,
    tenant_id: int,
) -> PurchaseOrder:
    purchase_order = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(
            PurchaseOrder.id == purchase_order_id,
            PurchaseOrder.tenant_id == tenant_id,
        )
        .first()
    )
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if (
        not _can_access_any_tenant_document(db, current_user)
        and purchase_order.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this purchase order"
        )
    return purchase_order


def submit_purchase_order_for_review(
    db: Session,
    current_user: User,
    purchase_order_id: int,
    action_in: PurchaseOrderReviewAction,
    tenant_id: int,
) -> PurchaseOrder:
    purchase_order = _get_purchase_order_for_user(
        db=db,
        current_user=current_user,
        purchase_order_id=purchase_order_id,
        tenant_id=tenant_id,
    )
    if purchase_order.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft purchase orders can be submitted for review",
        )

    purchase_order.status = "pending_review"
    purchase_order.review_note = action_in.review_note
    db.add(purchase_order)
    db.commit()
    db.refresh(purchase_order)
    return purchase_order


def mark_purchase_order_ordered(
    db: Session,
    current_user: User,
    purchase_order_id: int,
    action_in: PurchaseOrderReviewAction,
    tenant_id: int,
) -> PurchaseOrder:
    purchase_order = _get_purchase_order_for_user(
        db=db,
        current_user=current_user,
        purchase_order_id=purchase_order_id,
        tenant_id=tenant_id,
    )
    if purchase_order.status != "pending_review":
        raise HTTPException(
            status_code=400,
            detail="Only purchase orders pending review can be marked ordered",
        )
    if not current_user.is_superuser and purchase_order.user_id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Cannot approve a purchase order you created",
        )

    purchase_order.status = "ordered"
    purchase_order.ordered_at = datetime.now(UTC)
    purchase_order.review_note = action_in.review_note
    db.add(purchase_order)
    db.commit()
    db.refresh(purchase_order)
    return purchase_order


def reject_purchase_order(
    db: Session,
    current_user: User,
    purchase_order_id: int,
    action_in: PurchaseOrderReviewAction,
    tenant_id: int,
) -> PurchaseOrder:
    purchase_order = _get_purchase_order_for_user(
        db=db,
        current_user=current_user,
        purchase_order_id=purchase_order_id,
        tenant_id=tenant_id,
    )
    if purchase_order.status != "pending_review":
        raise HTTPException(
            status_code=400,
            detail="Only purchase orders pending review can be rejected",
        )
    if not current_user.is_superuser and purchase_order.user_id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Cannot reject a purchase order you created",
        )

    purchase_order.status = "rejected"
    purchase_order.review_note = action_in.review_note
    db.add(purchase_order)
    db.commit()
    db.refresh(purchase_order)
    return purchase_order


def cancel_purchase_order(
    db: Session,
    current_user: User,
    purchase_order_id: int,
    tenant_id: int,
) -> PurchaseOrder:
    purchase_order = _get_purchase_order_for_user(
        db=db,
        current_user=current_user,
        purchase_order_id=purchase_order_id,
        tenant_id=tenant_id,
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
    tenant_id: int,
) -> PurchaseOrder:
    if not receive_in.items:
        raise HTTPException(
            status_code=400, detail="Receive request must contain at least one item"
        )

    purchase_order = _get_purchase_order_for_user(
        db=db,
        current_user=current_user,
        purchase_order_id=purchase_order_id,
        tenant_id=tenant_id,
    )
    if purchase_order.status not in ("ordered", "partially_received"):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot receive items for a {purchase_order.status} purchase order"
            ),
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
        product = (
            db.query(Product)
            .filter(
                Product.id == po_item.product_id,
                Product.tenant_id == tenant_id,
            )
            .with_for_update()
            .first()
        )
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
                tenant_id=tenant_id,
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
        purchase_order.received_at = datetime.now(UTC)
    elif any_received:
        purchase_order.status = "partially_received"

    db.add(purchase_order)
    db.commit()

    return (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items))
        .filter(
            PurchaseOrder.id == purchase_order.id,
            PurchaseOrder.tenant_id == tenant_id,
        )
        .first()
    )


def _paid_total_for_invoice(db: Session, invoice: PurchaseInvoice) -> Decimal:
    return db.query(func.coalesce(func.sum(SupplierPayment.amount), 0)).filter(
        SupplierPayment.invoice_id == invoice.id,
        SupplierPayment.tenant_id == invoice.tenant_id,
        SupplierPayment.status == "approved",
    ).scalar() or Decimal("0")


def _attach_outstanding_amounts(
    db: Session, invoices: list[PurchaseInvoice], tenant_id: int
) -> None:
    """Set the computed outstanding_amount on each invoice in place.

    Bulk variant of _paid_total_for_invoice: a single grouped SUM over the
    approved supplier payments for all invoices at once, so list responses
    don't run one query per invoice.
    """
    invoice_ids = [invoice.id for invoice in invoices]
    if not invoice_ids:
        return
    paid_rows = (
        db.query(
            SupplierPayment.invoice_id,
            func.coalesce(func.sum(SupplierPayment.amount), 0),
        )
        .filter(
            SupplierPayment.invoice_id.in_(invoice_ids),
            SupplierPayment.tenant_id == tenant_id,
            SupplierPayment.status == "approved",
        )
        .group_by(SupplierPayment.invoice_id)
        .all()
    )
    paid_by_invoice = {invoice_id: paid for invoice_id, paid in paid_rows}
    for invoice in invoices:
        paid = to_decimal(paid_by_invoice.get(invoice.id, Decimal("0")))
        invoice.outstanding_amount = float(to_decimal(invoice.total_amount) - paid)


def _get_supplier_payment_for_user(
    db: Session,
    current_user: User,
    payment_id: int,
    tenant_id: int,
) -> SupplierPayment:
    payment = (
        db.query(SupplierPayment)
        .filter(
            SupplierPayment.id == payment_id,
            SupplierPayment.tenant_id == tenant_id,
        )
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Supplier payment not found")
    if (
        not _can_access_any_tenant_document(db, current_user)
        and payment.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this supplier payment"
        )
    return payment


def create_supplier_payment(
    db: Session,
    current_user: User,
    payment_in: SupplierPaymentCreate,
    tenant_id: int,
) -> SupplierPayment:
    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == payment_in.supplier_id,
            Supplier.tenant_id == tenant_id,
        )
        .first()
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if not supplier.is_active:
        raise HTTPException(status_code=400, detail="Supplier is inactive")

    invoice = (
        db.query(PurchaseInvoice)
        .filter(
            PurchaseInvoice.id == payment_in.invoice_id,
            PurchaseInvoice.tenant_id == tenant_id,
        )
        .with_for_update()
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Purchase invoice not found")
    if invoice.supplier_id != supplier.id:
        raise HTTPException(
            status_code=400,
            detail="Invoice does not belong to the selected supplier",
        )
    if invoice.status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Only approved invoices can be paid",
        )

    paid_total = _paid_total_for_invoice(db, invoice)
    outstanding = to_decimal(invoice.total_amount) - paid_total
    payment_amount = quantize_money(to_decimal(payment_in.amount))
    if payment_amount > outstanding:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Payment exceeds outstanding amount. Outstanding: "
                f"{outstanding}, payment: {payment_amount}"
            ),
        )

    payment = SupplierPayment(
        supplier_id=supplier.id,
        invoice_id=invoice.id,
        user_id=current_user.id,
        tenant_id=tenant_id,
        amount=payment_amount,
        payment_method=payment_in.payment_method.strip(),
        reference=payment_in.reference,
        status="draft",
        payment_date=payment_in.payment_date,
        notes=payment_in.notes,
    )
    if not payment.payment_method:
        raise HTTPException(status_code=400, detail="Payment method cannot be empty")

    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def submit_supplier_payment_for_review(
    db: Session,
    current_user: User,
    payment_id: int,
    action_in: SupplierPaymentReviewAction,
    tenant_id: int,
) -> SupplierPayment:
    payment = _get_supplier_payment_for_user(
        db=db,
        current_user=current_user,
        payment_id=payment_id,
        tenant_id=tenant_id,
    )
    if payment.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft payments can be submitted for review",
        )

    payment.status = "pending_review"
    payment.review_note = action_in.review_note
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def approve_supplier_payment(
    db: Session,
    current_user: User,
    payment_id: int,
    action_in: SupplierPaymentReviewAction,
    tenant_id: int,
) -> SupplierPayment:
    payment = _get_supplier_payment_for_user(
        db=db,
        current_user=current_user,
        payment_id=payment_id,
        tenant_id=tenant_id,
    )
    if payment.status != "pending_review":
        raise HTTPException(
            status_code=400,
            detail="Only pending_review payments can be approved",
        )
    if not current_user.is_superuser and payment.user_id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Cannot approve a supplier payment you created",
        )

    invoice = (
        db.query(PurchaseInvoice)
        .filter(
            PurchaseInvoice.id == payment.invoice_id,
            PurchaseInvoice.tenant_id == tenant_id,
        )
        .with_for_update()
        .first()
    )
    if not invoice or invoice.status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Payment can only be approved against an approved invoice",
        )

    paid_total = _paid_total_for_invoice(db, invoice)
    outstanding = to_decimal(invoice.total_amount) - paid_total
    if to_decimal(payment.amount) > outstanding:
        raise HTTPException(
            status_code=400,
            detail="Approving this payment would exceed the outstanding amount",
        )

    payment.status = "approved"
    payment.review_note = action_in.review_note
    payment.approved_at = datetime.now(UTC)
    payment.rejected_at = None
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def reject_supplier_payment(
    db: Session,
    current_user: User,
    payment_id: int,
    action_in: SupplierPaymentReviewAction,
    tenant_id: int,
) -> SupplierPayment:
    payment = _get_supplier_payment_for_user(
        db=db,
        current_user=current_user,
        payment_id=payment_id,
        tenant_id=tenant_id,
    )
    if payment.status != "pending_review":
        raise HTTPException(
            status_code=400,
            detail="Only pending_review payments can be rejected",
        )
    if not current_user.is_superuser and payment.user_id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Cannot reject a supplier payment you created",
        )

    payment.status = "rejected"
    payment.review_note = action_in.review_note
    payment.rejected_at = datetime.now(UTC)
    payment.approved_at = None
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_purchase_order_detail_data(
    db: Session, tenant_id: int, purchase_order_id: int
) -> dict:
    """Consolidated PO detail: per-item invoiced totals + lifecycle timeline."""
    purchase_order = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.items), joinedload(PurchaseOrder.invoices))
        .filter(
            PurchaseOrder.id == purchase_order_id,
            PurchaseOrder.tenant_id == tenant_id,
        )
        .first()
    )
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    item_ids = [item.id for item in purchase_order.items]
    invoiced_by_item: dict[int, tuple[int, float]] = {}
    if item_ids:
        rows = (
            db.query(
                PurchaseInvoiceItem.purchase_order_item_id,
                func.coalesce(func.sum(PurchaseInvoiceItem.billed_quantity), 0),
                func.coalesce(func.sum(PurchaseInvoiceItem.line_total), 0.0),
            )
            .join(PurchaseInvoice, PurchaseInvoiceItem.invoice_id == PurchaseInvoice.id)
            .filter(
                PurchaseInvoiceItem.purchase_order_item_id.in_(item_ids),
                PurchaseInvoiceItem.tenant_id == tenant_id,
                PurchaseInvoice.status != "rejected",
            )
            .group_by(PurchaseInvoiceItem.purchase_order_item_id)
            .all()
        )
        invoiced_by_item = {row[0]: (int(row[1]), float(row[2])) for row in rows}

    timeline = [
        {"event": "created", "at": purchase_order.created_at},
    ]
    if purchase_order.ordered_at:
        timeline.append({"event": "ordered", "at": purchase_order.ordered_at})
    receipts = (
        db.query(StockMovement)
        .filter(
            StockMovement.purchase_order_id == purchase_order.id,
            StockMovement.tenant_id == tenant_id,
            StockMovement.movement_type == "purchase_receipt",
        )
        .order_by(StockMovement.created_at.asc())
        .all()
    )
    for movement in receipts:
        timeline.append(
            {
                "event": "received",
                "at": movement.created_at,
                "note": f"+{movement.quantity_delta} units",
            }
        )
    for invoice in purchase_order.invoices:
        timeline.append(
            {
                "event": "invoice_created",
                "at": invoice.created_at,
                "note": f"{invoice.invoice_number} ({invoice.status})",
            }
        )
        if invoice.approved_at:
            timeline.append(
                {
                    "event": "invoice_approved",
                    "at": invoice.approved_at,
                    "note": invoice.invoice_number,
                }
            )
        if invoice.rejected_at:
            timeline.append(
                {
                    "event": "invoice_rejected",
                    "at": invoice.rejected_at,
                    "note": invoice.invoice_number,
                }
            )
    timeline.sort(key=lambda event: event["at"])

    total_received_amount = sum(
        float(item.quantity_received * item.unit_cost) for item in purchase_order.items
    )
    total_billed_amount = sum(billed for _, billed in invoiced_by_item.values())

    approved_invoice_total = sum(
        float(invoice.total_amount or 0)
        for invoice in purchase_order.invoices
        if invoice.status == "approved"
    )
    invoice_ids = [invoice.id for invoice in purchase_order.invoices]
    approved_payment_total = 0.0
    if invoice_ids:
        approved_payment_total = float(
            db.query(func.coalesce(func.sum(SupplierPayment.amount), 0.0))
            .filter(
                SupplierPayment.invoice_id.in_(invoice_ids),
                SupplierPayment.tenant_id == tenant_id,
                SupplierPayment.status == "approved",
            )
            .scalar()
            or 0.0
        )

    return {
        **{
            column: getattr(purchase_order, column)
            for column in (
                "id",
                "supplier_id",
                "user_id",
                "status",
                "total_estimated_amount",
                "notes",
                "review_note",
                "created_at",
                "ordered_at",
                "received_at",
            )
        },
        "items": [
            {
                "id": item.id,
                "purchase_order_id": item.purchase_order_id,
                "product_id": item.product_id,
                "quantity_ordered": item.quantity_ordered,
                "quantity_received": item.quantity_received,
                "unit_cost": float(item.unit_cost),
                "quantity_invoiced": invoiced_by_item.get(item.id, (0, 0.0))[0],
                "billed_total": invoiced_by_item.get(item.id, (0, 0.0))[1],
            }
            for item in purchase_order.items
        ],
        "timeline": timeline,
        "total_received_amount": total_received_amount,
        "total_billed_amount": total_billed_amount,
        "outstanding_payable": quantize_money(
            to_decimal(approved_invoice_total - approved_payment_total)
        ),
    }


def get_supplier_ledger_data(db: Session, tenant_id: int, supplier_id: int) -> dict:
    """Supplier ledger: open POs, pending invoices, payable totals, recent entries."""
    supplier = (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id, Supplier.tenant_id == tenant_id)
        .first()
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    open_statuses = ("draft", "pending_review", "ordered", "partially_received")
    open_po_count, open_po_amount = (
        db.query(
            func.count(PurchaseOrder.id),
            func.coalesce(func.sum(PurchaseOrder.total_estimated_amount), 0.0),
        )
        .filter(
            PurchaseOrder.tenant_id == tenant_id,
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.status.in_(open_statuses),
        )
        .first()
    )

    pending_invoice_count, pending_invoice_amount = (
        db.query(
            func.count(PurchaseInvoice.id),
            func.coalesce(func.sum(PurchaseInvoice.total_amount), 0.0),
        )
        .filter(
            PurchaseInvoice.tenant_id == tenant_id,
            PurchaseInvoice.supplier_id == supplier_id,
            PurchaseInvoice.status == "pending_review",
        )
        .first()
    )

    approved_invoice_total = float(
        db.query(func.coalesce(func.sum(PurchaseInvoice.total_amount), 0.0))
        .filter(
            PurchaseInvoice.tenant_id == tenant_id,
            PurchaseInvoice.supplier_id == supplier_id,
            PurchaseInvoice.status == "approved",
        )
        .scalar()
        or 0.0
    )
    approved_payment_total = float(
        db.query(func.coalesce(func.sum(SupplierPayment.amount), 0.0))
        .filter(
            SupplierPayment.tenant_id == tenant_id,
            SupplierPayment.supplier_id == supplier_id,
            SupplierPayment.status == "approved",
        )
        .scalar()
        or 0.0
    )

    entries: list[dict] = []
    open_orders = (
        db.query(PurchaseOrder)
        .filter(
            PurchaseOrder.tenant_id == tenant_id,
            PurchaseOrder.supplier_id == supplier_id,
        )
        .order_by(PurchaseOrder.id.desc())
        .limit(20)
        .all()
    )
    for order in open_orders:
        entries.append(
            {
                "kind": "purchase_order",
                "id": order.id,
                "status": order.status,
                "amount": float(order.total_estimated_amount or 0),
                "date": order.created_at,
                "reference": f"PO-{order.id}",
            }
        )
    invoices = (
        db.query(PurchaseInvoice)
        .filter(
            PurchaseInvoice.tenant_id == tenant_id,
            PurchaseInvoice.supplier_id == supplier_id,
        )
        .order_by(PurchaseInvoice.id.desc())
        .limit(20)
        .all()
    )
    for invoice in invoices:
        entries.append(
            {
                "kind": "invoice",
                "id": invoice.id,
                "status": invoice.status,
                "amount": float(invoice.total_amount or 0),
                "date": invoice.created_at,
                "reference": invoice.invoice_number,
            }
        )
    payments = (
        db.query(SupplierPayment)
        .filter(
            SupplierPayment.tenant_id == tenant_id,
            SupplierPayment.supplier_id == supplier_id,
        )
        .order_by(SupplierPayment.id.desc())
        .limit(20)
        .all()
    )
    for payment in payments:
        entries.append(
            {
                "kind": "payment",
                "id": payment.id,
                "status": payment.status,
                "amount": float(payment.amount or 0),
                "date": payment.created_at,
                "reference": payment.reference or payment.payment_method,
            }
        )
    entries.sort(key=lambda entry: entry["date"], reverse=True)

    return {
        "supplier_id": supplier.id,
        "supplier_name": supplier.name,
        "open_purchase_orders": int(open_po_count or 0),
        "open_po_amount": float(open_po_amount or 0.0),
        "pending_invoice_count": int(pending_invoice_count or 0),
        "pending_invoice_amount": float(pending_invoice_amount or 0.0),
        "approved_invoice_total": approved_invoice_total,
        "approved_payment_total": approved_payment_total,
        "outstanding_payable": quantize_money(
            to_decimal(approved_invoice_total - approved_payment_total)
        ),
        "entries": entries[:50],
    }
