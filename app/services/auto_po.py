"""Scheduled auto-generation of purchase orders from replenishment suggestions.

Runs on an interval (REPLENISHMENT_AUTO_PO_ENABLED). For every product past
its reorder point, picks the supplier most recently used for that product
(from purchase orders/invoices), skips products already covered by a pending
PO, and creates one draft purchase order per supplier. The PO is attributed
to the first active superuser (same pattern as the reservation sweep).
"""
from collections import defaultdict
from typing import Dict, List

from sqlalchemy.orm import Session

from app.core.replenishment import build_replenishment_suggestions
from app.models.product import Product
from app.models.purchase import (
    PurchaseInvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)
from app.models.user import User
from app.schemas.replenishment import PurchaseOrderFromSuggestionsCreate
from app.services.purchasing import create_purchase_order_from_replenishment

_PENDING_STATUSES = ("draft", "ordered", "partially_received")


def _supplier_for_products(db: Session, product_ids: List[int]) -> Dict[int, int]:
    """Most recently used supplier per product (by purchase order id)."""
    rows = (
        db.query(PurchaseOrderItem.product_id, PurchaseOrder.supplier_id)
        .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
        .filter(PurchaseOrderItem.product_id.in_(product_ids))
        .order_by(PurchaseOrder.id.desc())
        .all()
    )
    supplier_map: Dict[int, int] = {}
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
    return supplier_map


def _products_already_in_pending_po(db: Session) -> set[int]:
    rows = (
        db.query(PurchaseOrderItem.product_id)
        .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
        .filter(PurchaseOrder.status.in_(_PENDING_STATUSES))
        .all()
    )
    return {row[0] for row in rows}


def auto_generate_purchase_orders(
    db: Session,
    lookback_days: int = 30,
) -> dict:
    """Create draft POs for products past reorder point. Idempotent per run."""
    pending_products = _products_already_in_pending_po(db)
    candidates = (
        db.query(Product)
        .filter(Product.stock_quantity <= Product.reorder_point)
        .order_by(Product.id.asc())
        .all()
    )
    candidates = [p for p in candidates if p.id not in pending_products]
    if not candidates:
        return {"generated": 0, "skipped_products": [], "po_ids": [], "suppliers": []}

    actor = (
        db.query(User)
        .filter(User.is_superuser.is_(True), User.is_active.is_(True))
        .order_by(User.id.asc())
        .first()
    )
    if not actor:
        return {
            "generated": 0,
            "skipped_products": [
                {"product_id": p.id, "reason": "no active superuser to own the PO"}
                for p in candidates
            ],
            "po_ids": [],
            "suppliers": [],
        }

    suggestions = build_replenishment_suggestions(
        db=db, products=candidates, lookback_days=lookback_days
    )
    reorder_items = [
        item
        for item in suggestions
        if item.should_reorder and item.recommended_order_quantity > 0
    ]
    if not reorder_items:
        return {"generated": 0, "skipped_products": [], "po_ids": [], "suppliers": []}

    product_ids = [item.product_id for item in reorder_items]
    supplier_map = _supplier_for_products(db, product_ids)

    by_supplier: Dict[int, List[int]] = defaultdict(list)
    skipped: List[dict] = []
    for item in reorder_items:
        supplier_id = supplier_map.get(item.product_id)
        if supplier_id is None:
            skipped.append(
                {"product_id": item.product_id, "reason": "no supplier history"}
            )
            continue
        by_supplier[supplier_id].append(item.product_id)

    po_ids: List[int] = []
    generated_suppliers: List[str] = []
    for supplier_id, supplier_product_ids in by_supplier.items():
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier or not supplier.is_active:
            for product_id in supplier_product_ids:
                skipped.append(
                    {"product_id": product_id, "reason": "supplier inactive"}
                )
            continue
        purchase_order = create_purchase_order_from_replenishment(
            db=db,
            current_user=actor,
            payload=PurchaseOrderFromSuggestionsCreate(
                supplier_id=supplier_id,
                lookback_days=lookback_days,
                product_ids=supplier_product_ids,
                include_only_reorder=True,
                notes=(
                    f"Auto-generated by scheduled replenishment "
                    f"(lookback_days={lookback_days})"
                ),
            ),
        )
        po_ids.append(purchase_order.id)
        generated_suppliers.append(supplier.name)

    return {
        "generated": len(po_ids),
        "skipped_products": skipped,
        "po_ids": po_ids,
        "suppliers": generated_suppliers,
    }
