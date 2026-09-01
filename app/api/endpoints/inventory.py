from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import require_permissions
from app.core.audit import log_action
from app.core.database import get_db
from app.core.replenishment import build_replenishment_suggestions
from app.models.product import Product
from app.models.purchase import Supplier
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.replenishment import ReplenishmentSuggestion
from app.schemas.stock_movement import (
    InventoryReceiptCreate,
)
from app.schemas.stock_movement import (
    StockMovement as StockMovementSchema,
)
from app.services.purchasing import supplier_map_with_names

router = APIRouter()


@router.get("/movements", response_model=list[StockMovementSchema])
def get_inventory_movements(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    product_id: int | None = Query(None, ge=1),
    movement_type: str | None = Query(None),
    user_id: int | None = Query(None, ge=1),
    purchase_order_id: int | None = Query(None, ge=1),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    current_user: User = Depends(require_permissions("inventory:view")),
):
    query = (
        db.query(StockMovement)
        .options(joinedload(StockMovement.product), joinedload(StockMovement.user))
        .filter(StockMovement.tenant_id == current_user.tenant_id)
        .order_by(StockMovement.id.desc())
    )

    if product_id:
        query = query.filter(StockMovement.product_id == product_id)
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)
    if user_id:
        query = query.filter(StockMovement.user_id == user_id)
    if purchase_order_id:
        query = query.filter(StockMovement.purchase_order_id == purchase_order_id)
    if start_date:
        query = query.filter(StockMovement.created_at >= start_date)
    if end_date:
        query = query.filter(StockMovement.created_at <= end_date)

    movements = query.offset(skip).limit(limit).all()
    # Enrich with product/user details for intuitive UI
    for m in movements:
        if m.product:
            m.product_name = m.product.name  # type: ignore[attr-defined]
            m.product_sku = m.product.sku  # type: ignore[attr-defined]
        if m.user:
            m.user_email = m.user.email  # type: ignore[attr-defined]
    return movements


@router.post("/receipt", response_model=StockMovementSchema)
def create_inventory_receipt(
    payload: InventoryReceiptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("inventory:view")),
):
    """Ad-hoc stock receipt without a purchase order (intuitive restock)."""
    product = (
        db.query(Product)
        .filter(
            Product.id == payload.product_id,
            Product.tenant_id == current_user.tenant_id,
        )
        .with_for_update()
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found") from None

    supplier_id = payload.supplier_id
    if supplier_id is not None:
        supplier = (
            db.query(Supplier)
            .filter(
                Supplier.id == supplier_id, Supplier.tenant_id == current_user.tenant_id
            )
            .first()
        )
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found") from None
        if not supplier.is_active:
            raise HTTPException(
                status_code=400, detail="Supplier is inactive"
            ) from None

    quantity_before = product.stock_quantity
    quantity_after = quantity_before + payload.quantity
    product.stock_quantity = quantity_after
    if payload.unit_cost is not None:
        product.unit_cost = payload.unit_cost
    db.add(product)

    movement = StockMovement(
        product_id=product.id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        movement_type="ad_hoc_receipt",
        quantity_before=quantity_before,
        quantity_delta=payload.quantity,
        quantity_after=quantity_after,
        note=payload.note or "Ad-hoc stock receipt",
    )
    db.add(movement)
    log_action(
        db=db,
        action="inventory.ad_hoc_receipt",
        user_id=current_user.id,
        resource_type="product",
        resource_id=product.id,
        details={
            "quantity_before": quantity_before,
            "quantity_after": quantity_after,
            "delta": payload.quantity,
            "supplier_id": supplier_id,
            "unit_cost": payload.unit_cost,
            "note": payload.note,
        },
    )
    db.commit()
    db.refresh(movement)
    # Enrich for response
    movement.product_name = product.name  # type: ignore[attr-defined]
    movement.product_sku = product.sku  # type: ignore[attr-defined]
    movement.user_email = current_user.email  # type: ignore[attr-defined]
    return movement


@router.get("/replenishment-suggestions", response_model=list[ReplenishmentSuggestion])
def get_replenishment_suggestions(
    db: Session = Depends(get_db),
    lookback_days: int = Query(30, ge=1, le=365),
    product_id: int | None = Query(None, ge=1),
    only_reorder_needed: bool = Query(True),
    current_user: User = Depends(require_permissions("inventory:view")),
):
    query = (
        db.query(Product)
        .filter(Product.tenant_id == current_user.tenant_id)
        .order_by(Product.id.asc())
    )
    if product_id is not None:
        query = query.filter(
            Product.id == product_id,
            Product.tenant_id == current_user.tenant_id,
        )

    products = query.all()
    suggestions = build_replenishment_suggestions(
        db=db,
        products=products,
        lookback_days=lookback_days,
        supplier_map=supplier_map_with_names(
            db, [product.id for product in products], tenant_id=current_user.tenant_id
        ),
    )

    if only_reorder_needed:
        suggestions = [item for item in suggestions if item.should_reorder]

    return sorted(
        suggestions,
        key=lambda item: (
            item.recommended_order_quantity,
            item.current_stock,
        ),
        reverse=True,
    )
