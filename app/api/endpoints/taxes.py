from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.product import Category, Product
from app.models.tax import TaxRule
from app.models.user import User
from app.schemas.tax import TaxRule as TaxRuleSchema
from app.schemas.tax import TaxRuleCreate, TaxRuleUpdate

router = APIRouter()


def _validate_tax_scope(db: Session, tax_data: dict) -> None:
    tax_scope = tax_data.get("tax_scope")
    product_id = tax_data.get("product_id")
    category_id = tax_data.get("category_id")

    if tax_scope not in ("order", "product", "category"):
        raise HTTPException(
            status_code=400,
            detail="Invalid tax_scope. Must be one of: order, product, category",
        )

    if tax_scope == "product":
        if not product_id:
            raise HTTPException(
                status_code=400, detail="product_id is required when tax_scope=product"
            )
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
    elif tax_scope == "category":
        if not category_id:
            raise HTTPException(
                status_code=400,
                detail="category_id is required when tax_scope=category",
            )
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    else:
        if product_id is not None or category_id is not None:
            raise HTTPException(
                status_code=400,
                detail="product_id/category_id must be null when tax_scope=order",
            )


def _validate_tax_mode(tax_data: dict) -> None:
    tax_mode = tax_data.get("tax_mode")
    if tax_mode not in ("exclusive", "inclusive"):
        raise HTTPException(
            status_code=400,
            detail="Invalid tax_mode. Must be one of: exclusive, inclusive",
        )


def _validate_tax_dates(tax_data: dict) -> None:
    starts_at = tax_data.get("starts_at")
    ends_at = tax_data.get("ends_at")
    if starts_at and ends_at and starts_at > ends_at:
        raise HTTPException(status_code=400, detail="starts_at cannot be after ends_at")


@router.get("/", response_model=List[TaxRuleSchema])
def get_tax_rules(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    return db.query(TaxRule).offset(skip).limit(limit).all()


@router.get("/{tax_rule_id}", response_model=TaxRuleSchema)
def get_tax_rule(
    tax_rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    tax_rule = db.query(TaxRule).filter(TaxRule.id == tax_rule_id).first()
    if not tax_rule:
        raise HTTPException(status_code=404, detail="Tax rule not found")
    return tax_rule


@router.post("/", response_model=TaxRuleSchema)
def create_tax_rule(
    tax_in: TaxRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    tax_data = tax_in.model_dump()
    _validate_tax_scope(db, tax_data)
    _validate_tax_mode(tax_data)
    _validate_tax_dates(tax_data)

    tax_rule = TaxRule(**tax_data)
    db.add(tax_rule)
    db.commit()
    db.refresh(tax_rule)
    return tax_rule


@router.put("/{tax_rule_id}", response_model=TaxRuleSchema)
def update_tax_rule(
    tax_rule_id: int,
    tax_in: TaxRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    tax_rule = db.query(TaxRule).filter(TaxRule.id == tax_rule_id).first()
    if not tax_rule:
        raise HTTPException(status_code=404, detail="Tax rule not found")

    update_data = tax_in.model_dump(exclude_unset=True)
    merged_data = {
        "tax_scope": tax_rule.tax_scope,
        "tax_mode": tax_rule.tax_mode,
        "product_id": tax_rule.product_id,
        "category_id": tax_rule.category_id,
        "starts_at": tax_rule.starts_at,
        "ends_at": tax_rule.ends_at,
    }
    merged_data.update(update_data)

    _validate_tax_scope(db, merged_data)
    _validate_tax_mode(merged_data)
    _validate_tax_dates(merged_data)

    for field, value in update_data.items():
        setattr(tax_rule, field, value)
    db.add(tax_rule)
    db.commit()
    db.refresh(tax_rule)
    return tax_rule


@router.delete("/{tax_rule_id}")
def deactivate_tax_rule(
    tax_rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    tax_rule = db.query(TaxRule).filter(TaxRule.id == tax_rule_id).first()
    if not tax_rule:
        raise HTTPException(status_code=404, detail="Tax rule not found")

    tax_rule.is_active = False
    tax_rule.ends_at = tax_rule.ends_at or datetime.now(timezone.utc)
    db.add(tax_rule)
    db.commit()
    return {"ok": True}
