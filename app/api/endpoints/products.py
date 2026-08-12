from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, require_permissions
from app.core.database import get_db
from app.models.order import OrderItem
from app.models.product import Category, Product
from app.models.purchase import PurchaseInvoiceItem, PurchaseOrderItem
from app.models.refund import RefundItem
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.product import Category as CategorySchema
from app.schemas.product import CategoryCreate
from app.schemas.product import Product as ProductSchema
from app.schemas.product import ProductCreate, ProductUpdate

router = APIRouter()

# Category Endpoints


@router.get("/categories", response_model=List[CategorySchema])
def get_categories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories


@router.post("/categories", response_model=CategorySchema)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("products:manage")),
):
    category = Category(**category_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("products:manage")),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    product_count = (
        db.query(func.count(Product.id))
        .filter(Product.category_id == category_id)
        .scalar()
    )
    if product_count:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot delete category with {product_count} product(s) assigned "
                "to it. Reassign or delete those products first."
            ),
        )

    db.delete(category)
    db.commit()
    return {"ok": True}


# Product Endpoints


@router.get("/", response_model=List[ProductSchema])
def get_products(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


@router.post("/", response_model=ProductSchema)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("products:manage")),
):
    # check category if provided
    if product_in.category_id:
        category = (
            db.query(Category).filter(Category.id == product_in.category_id).first()
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    product = Product(**product_in.model_dump())
    db.add(product)
    db.flush()

    if product.stock_quantity:
        db.add(
            StockMovement(
                product_id=product.id,
                user_id=current_user.id,
                movement_type="initial_stock",
                quantity_before=0,
                quantity_delta=product.stock_quantity,
                quantity_after=product.stock_quantity,
                note="Initial stock set on product creation",
            )
        )

    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductSchema)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("products:manage")),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_in.model_dump(exclude_unset=True)
    previous_stock_quantity = product.stock_quantity
    for field, value in update_data.items():
        setattr(product, field, value)

    db.add(product)
    stock_changed = "stock_quantity" in update_data and (
        product.stock_quantity != previous_stock_quantity
    )
    if stock_changed:
        db.add(
            StockMovement(
                product_id=product.id,
                user_id=current_user.id,
                movement_type="manual_adjustment",
                quantity_before=previous_stock_quantity,
                quantity_delta=product.stock_quantity - previous_stock_quantity,
                quantity_after=product.stock_quantity,
                note="Stock quantity updated from product endpoint",
            )
        )

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("products:manage")),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reference_counts = {
        "order item": db.query(func.count(OrderItem.id))
        .filter(OrderItem.product_id == product_id)
        .scalar(),
        "stock movement": db.query(func.count(StockMovement.id))
        .filter(StockMovement.product_id == product_id)
        .scalar(),
        "purchase order item": db.query(func.count(PurchaseOrderItem.id))
        .filter(PurchaseOrderItem.product_id == product_id)
        .scalar(),
        "purchase invoice item": db.query(func.count(PurchaseInvoiceItem.id))
        .filter(PurchaseInvoiceItem.product_id == product_id)
        .scalar(),
        "refund item": db.query(func.count(RefundItem.id))
        .filter(RefundItem.product_id == product_id)
        .scalar(),
    }
    referenced = {name: count for name, count in reference_counts.items() if count > 0}
    if referenced:
        details = ", ".join(f"{count} {name}(s)" for name, count in referenced.items())
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot delete product: referenced by {details}. "
                "Remove the references first."
            ),
        )

    db.delete(product)
    db.commit()
    return {"ok": True}
