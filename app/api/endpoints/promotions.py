from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, require_permissions
from app.core.database import get_db
from app.models.product import Category, Product
from app.models.promotion import Promotion
from app.models.user import User
from app.schemas.promotion import Promotion as PromotionSchema
from app.schemas.promotion import PromotionCreate, PromotionUpdate

router = APIRouter()


def _validate_promotion_scope(
    db: Session, promotion_data: dict, tenant_id: int
) -> None:
    applies_to = promotion_data.get("applies_to")
    product_id = promotion_data.get("product_id")
    category_id = promotion_data.get("category_id")

    if applies_to not in ("order", "product", "category"):
        raise HTTPException(
            status_code=400,
            detail="Invalid applies_to. Must be one of: order, product, category",
        )

    if applies_to == "product":
        if not product_id:
            raise HTTPException(
                status_code=400, detail="product_id is required when applies_to=product"
            )
        product = (
            db.query(Product)
            .filter(Product.id == product_id, Product.tenant_id == tenant_id)
            .first()
        )
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
    elif applies_to == "category":
        if not category_id:
            raise HTTPException(
                status_code=400,
                detail="category_id is required when applies_to=category",
            )
        category = (
            db.query(Category)
            .filter(Category.id == category_id, Category.tenant_id == tenant_id)
            .first()
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    else:
        if product_id is not None or category_id is not None:
            raise HTTPException(
                status_code=400,
                detail="product_id/category_id must be null when applies_to=order",
            )


def _validate_promotion_dates(promotion_data: dict) -> None:
    starts_at = promotion_data.get("starts_at")
    ends_at = promotion_data.get("ends_at")
    if starts_at and ends_at and starts_at > ends_at:
        raise HTTPException(status_code=400, detail="starts_at cannot be after ends_at")


def _validate_promotion_discount(promotion_data: dict) -> None:
    discount_type = promotion_data.get("discount_type")
    if discount_type not in ("percentage", "fixed"):
        raise HTTPException(
            status_code=400,
            detail="Invalid discount_type. Must be one of: percentage, fixed",
        )
    discount_value = promotion_data.get("discount_value")
    if discount_type == "percentage" and discount_value > 100:
        raise HTTPException(
            status_code=400,
            detail="Percentage discount_value cannot be greater than 100",
        )


@router.get("/", response_model=List[PromotionSchema])
def get_promotions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    return (
        db.query(Promotion)
        .filter(Promotion.tenant_id == current_user.tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{promotion_id}", response_model=PromotionSchema)
def get_promotion(
    promotion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    promotion = (
        db.query(Promotion)
        .filter(
            Promotion.id == promotion_id,
            Promotion.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return promotion


@router.post("/", response_model=PromotionSchema)
def create_promotion(
    promotion_in: PromotionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("promotions:manage")),
):
    promotion_data = promotion_in.model_dump()
    promotion_data["code"] = promotion_data["code"].strip().upper()

    existing = (
        db.query(Promotion)
        .filter(
            Promotion.code == promotion_data["code"],
            Promotion.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Promotion code already exists")

    _validate_promotion_scope(db, promotion_data, current_user.tenant_id)
    _validate_promotion_dates(promotion_data)
    _validate_promotion_discount(promotion_data)

    promotion = Promotion(**promotion_data, tenant_id=current_user.tenant_id)
    db.add(promotion)
    db.commit()
    db.refresh(promotion)
    return promotion


@router.put("/{promotion_id}", response_model=PromotionSchema)
def update_promotion(
    promotion_id: int,
    promotion_in: PromotionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("promotions:manage")),
):
    promotion = (
        db.query(Promotion)
        .filter(
            Promotion.id == promotion_id,
            Promotion.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")

    update_data = promotion_in.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"] is not None:
        update_data["code"] = update_data["code"].strip().upper()
        existing = (
            db.query(Promotion)
            .filter(
                Promotion.code == update_data["code"],
                Promotion.id != promotion_id,
                Promotion.tenant_id == current_user.tenant_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Promotion code already exists")

    merged_data = {
        "applies_to": promotion.applies_to,
        "product_id": promotion.product_id,
        "category_id": promotion.category_id,
        "starts_at": promotion.starts_at,
        "ends_at": promotion.ends_at,
        "discount_type": promotion.discount_type,
        "discount_value": promotion.discount_value,
    }
    merged_data.update(update_data)

    _validate_promotion_scope(db, merged_data, current_user.tenant_id)
    _validate_promotion_dates(merged_data)
    _validate_promotion_discount(merged_data)

    for field, value in update_data.items():
        setattr(promotion, field, value)

    db.add(promotion)
    db.commit()
    db.refresh(promotion)
    return promotion


@router.delete("/{promotion_id}")
def deactivate_promotion(
    promotion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("promotions:manage")),
):
    promotion = (
        db.query(Promotion)
        .filter(
            Promotion.id == promotion_id,
            Promotion.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")

    promotion.is_active = False
    promotion.ends_at = promotion.ends_at or datetime.now(timezone.utc)
    db.add(promotion)
    db.commit()
    return {"ok": True}
