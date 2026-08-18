from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_permissions
from app.core.database import get_db
from app.core.replenishment import build_replenishment_suggestions
from app.models.product import Product
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.replenishment import ReplenishmentSuggestion
from app.schemas.stock_movement import StockMovement as StockMovementSchema

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

    return query.offset(skip).limit(limit).all()


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
