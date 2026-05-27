from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.stock_movement import StockMovement as StockMovementSchema

router = APIRouter()


@router.get("/movements", response_model=List[StockMovementSchema])
def get_inventory_movements(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[int] = Query(None, ge=1),
    movement_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None, ge=1),
    purchase_order_id: Optional[int] = Query(None, ge=1),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(StockMovement).order_by(StockMovement.id.desc())

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
