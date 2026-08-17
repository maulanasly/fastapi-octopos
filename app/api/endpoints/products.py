import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.admin.color_field import CATEGORY_COLOR_PALETTE
from app.api.dependencies import get_current_active_user, require_permissions
from app.core.audit import log_action
from app.core.config import settings
from app.core.database import get_db
from app.models.order import OrderItem
from app.models.product import Category, Product
from app.models.purchase import PurchaseInvoiceItem, PurchaseOrderItem
from app.models.refund import RefundItem
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.product import Category as CategorySchema
from app.schemas.product import CategoryCreate, CategoryUpdate
from app.schemas.product import Product as ProductSchema
from app.schemas.product import ProductCreate, ProductUpdate

router = APIRouter()

# Category Endpoints


@router.get("/categories/colors", response_model=List[str])
def get_category_color_palette(
    current_user: User = Depends(get_current_active_user),
):
    """Curated category color palette (shared with the client)."""
    return CATEGORY_COLOR_PALETTE


@router.get("/categories", response_model=List[CategorySchema])
def get_categories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
):
    categories = (
        db.query(Category)
        .filter(Category.tenant_id == current_user.tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return categories


@router.post("/categories", response_model=CategorySchema)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("products:manage")),
):
    category = Category(**category_in.model_dump(), tenant_id=current_user.tenant_id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=CategorySchema)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("products:manage")),
):
    category = (
        db.query(Category)
        .filter(
            Category.id == category_id,
            Category.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = category_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
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
    category = (
        db.query(Category)
        .filter(
            Category.id == category_id,
            Category.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    product_count = (
        db.query(func.count(Product.id))
        .filter(
            Product.category_id == category_id,
            Product.tenant_id == current_user.tenant_id,
        )
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
    products = (
        db.query(Product)
        .filter(Product.tenant_id == current_user.tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
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
            db.query(Category)
            .filter(
                Category.id == product_in.category_id,
                Category.tenant_id == current_user.tenant_id,
            )
            .first()
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    product = Product(**product_in.model_dump(), tenant_id=current_user.tenant_id)
    db.add(product)
    db.flush()

    if product.stock_quantity:
        db.add(
            StockMovement(
                product_id=product.id,
                tenant_id=current_user.tenant_id,
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
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.tenant_id == current_user.tenant_id,
        )
        .with_for_update()
        .first()
    )
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
                tenant_id=current_user.tenant_id,
                user_id=current_user.id,
                movement_type="manual_adjustment",
                quantity_before=previous_stock_quantity,
                quantity_delta=product.stock_quantity - previous_stock_quantity,
                quantity_after=product.stock_quantity,
                note="Stock quantity updated from product endpoint",
            )
        )
        log_action(
            db=db,
            action="product.stock_adjust",
            user_id=current_user.id,
            resource_type="product",
            resource_id=product.id,
            details={
                "quantity_before": previous_stock_quantity,
                "quantity_after": product.stock_quantity,
            },
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
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reference_counts = {
        "order item": db.query(func.count(OrderItem.id))
        .filter(
            OrderItem.product_id == product_id,
            OrderItem.tenant_id == current_user.tenant_id,
        )
        .scalar(),
        "stock movement": db.query(func.count(StockMovement.id))
        .filter(
            StockMovement.product_id == product_id,
            StockMovement.tenant_id == current_user.tenant_id,
        )
        .scalar(),
        "purchase order item": db.query(func.count(PurchaseOrderItem.id))
        .filter(
            PurchaseOrderItem.product_id == product_id,
            PurchaseOrderItem.tenant_id == current_user.tenant_id,
        )
        .scalar(),
        "purchase invoice item": db.query(func.count(PurchaseInvoiceItem.id))
        .filter(
            PurchaseInvoiceItem.product_id == product_id,
            PurchaseInvoiceItem.tenant_id == current_user.tenant_id,
        )
        .scalar(),
        "refund item": db.query(func.count(RefundItem.id))
        .filter(
            RefundItem.product_id == product_id,
            RefundItem.tenant_id == current_user.tenant_id,
        )
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


# Image Endpoints

_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _media_dir() -> Path:
    path = Path(settings.MEDIA_DIR).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _delete_stored_image(image_url: Optional[str]) -> None:
    if not image_url or not image_url.startswith("/media/"):
        return
    try:
        file_path = (_media_dir() / image_url.removeprefix("/media/")).resolve()
        if file_path.is_file() and file_path.is_relative_to(_media_dir()):
            file_path.unlink()
    except OSError:
        pass


@router.post("/{product_id}/image", response_model=ProductSchema)
def upload_product_image(
    product_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("products:manage")),
):
    """Upload or replace a product photo (jpeg/png/webp, max 5 MB)."""
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    content_type = (file.content_type or "").lower()
    if content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported image type. Allowed: {sorted(_ALLOWED_IMAGE_TYPES)}",
        )

    content = file.file.read(_MAX_IMAGE_BYTES + 1)
    if len(content) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 5 MB limit")

    extension = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[
        content_type
    ]
    media_dir = _media_dir()
    (media_dir / "products").mkdir(parents=True, exist_ok=True)
    file_name = f"{product_id}_{uuid.uuid4().hex}.{extension}"
    destination = media_dir / "products" / file_name

    with destination.open("wb") as out:
        out.write(content)

    _delete_stored_image(product.image_url)
    product.image_url = f"/media/products/{file_name}"
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}/image", response_model=ProductSchema)
def delete_product_image(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("products:manage")),
):
    """Remove the product photo."""
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    _delete_stored_image(product.image_url)
    product.image_url = None
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
