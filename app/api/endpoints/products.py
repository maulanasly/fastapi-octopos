import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

from app.admin.color_field import CATEGORY_COLOR_PALETTE
from app.api.dependencies import get_current_active_user, require_permissions
from app.core.audit import log_action
from app.core.database import get_db
from app.models.order import OrderItem
from app.models.product import Category, Product
from app.models.purchase import PurchaseInvoiceItem, PurchaseOrderItem
from app.models.refund import RefundItem
from app.models.stock_movement import StockMovement
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.product import Category as CategorySchema
from app.schemas.product import (
    CategoryCreate,
    CategoryUpdate,
    ProductCreate,
    ProductUpdate,
)
from app.schemas.product import Product as ProductSchema
from app.services.embeddings import embed_text
from app.services.images import (
    _ALLOWED_IMAGE_TYPES,
    _MAX_IMAGE_BYTES,
    delete_media_file,
    process_product_image,
    product_media_dir,
)

router = APIRouter()

# Category Endpoints


@router.get("/categories/colors", response_model=list[str])
def get_category_color_palette(
    current_user: User = Depends(get_current_active_user),
):
    """Curated category color palette (shared with the client)."""
    return CATEGORY_COLOR_PALETTE


@router.get("/categories", response_model=list[CategorySchema])
def get_categories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    tenant_id: int | None = Query(None, description="Tenant filter (superuser only)"),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(Category).filter(Category.deleted_at.is_(None))
    if current_user.is_superuser:
        if tenant_id is not None:
            query = query.filter(Category.tenant_id == tenant_id)
    else:
        query = query.filter(Category.tenant_id == current_user.tenant_id)
    categories = query.offset(skip).limit(limit).all()
    return categories


@router.post("/categories", response_model=CategorySchema)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    tenant_id: int | None = Query(None, description="Tenant filter (superuser only)"),
    current_user: User = Depends(require_permissions("products:manage")),
):
    if current_user.is_superuser:
        effective_tenant = (
            tenant_id if tenant_id is not None else current_user.tenant_id
        )
    else:
        effective_tenant = current_user.tenant_id
    if effective_tenant is None:
        raise HTTPException(
            status_code=400, detail="tenant_id is required for superuser"
        ) from None
    category = Category(**category_in.model_dump(), tenant_id=effective_tenant)
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
    q = db.query(Category).filter(Category.id == category_id)
    if not current_user.is_superuser:
        q = q.filter(Category.tenant_id == current_user.tenant_id)
    category = q.first()
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
    q = db.query(Category).filter(Category.id == category_id)
    if not current_user.is_superuser:
        q = q.filter(Category.tenant_id == current_user.tenant_id)
    category = q.first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Count products in the same tenant as the category (or all if superuser unscoped)
    count_q = db.query(func.count(Product.id)).filter(
        Product.category_id == category_id,
        Product.deleted_at.is_(None),
    )
    if not current_user.is_superuser:
        count_q = count_q.filter(Product.tenant_id == current_user.tenant_id)
    else:
        # Superuser: count within the category's tenant to avoid cross-tenant block
        count_q = count_q.filter(Product.tenant_id == category.tenant_id)
    product_count = count_q.scalar()
    if product_count:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot delete category with {product_count} product(s) assigned "
                "to it. Reassign or delete those products first."
            ),
        )

    category.deleted_at = datetime.now(UTC)
    category.updated_at = datetime.now(UTC)
    db.add(category)
    db.commit()
    return {"ok": True}


# Product Endpoints


@router.get("/search", response_model=list[ProductSchema])
def search_products(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=100),
    tenant_id: int | None = Query(None, description="Tenant filter (superuser only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Semantic catalog search over product embeddings (pgvector).

    Requires embeddings to be configured and populated (products created
    or updated after the embedding feature, or the backfill script run).
    Returns 400 when embeddings are disabled or no product has an
    embedding yet.
    """
    vector = embed_text(q)
    if vector is None:
        raise HTTPException(
            status_code=400,
            detail="Semantic search is not configured (EMBEDDING_PROVIDER=none)",
        )
    # Superuser bypass: no tenant filter when tenant_id is None, else filter to that tenant.
    # Normal users always filter to their own tenant (ignore query param).
    effective_tenant: int | None
    if current_user.is_superuser:
        effective_tenant = tenant_id
    else:
        effective_tenant = current_user.tenant_id

    if effective_tenant is None:
        # Superuser unscoped search
        products = (
            db.execute(
                text(
                    """
                SELECT * FROM products
                WHERE embedding IS NOT NULL
                  AND deleted_at IS NULL
                ORDER BY embedding <=> :query
                LIMIT :limit
                """
                ),
                {
                    "query": "[" + ",".join(repr(v) for v in vector) + "]",
                    "limit": limit,
                },
            )
            .mappings()
            .all()
        )
    else:
        products = (
            db.execute(
                text(
                    """
                SELECT * FROM products
                WHERE tenant_id = :tenant_id
                  AND embedding IS NOT NULL
                  AND deleted_at IS NULL
                ORDER BY embedding <=> :query
                LIMIT :limit
                """
                ),
                {
                    "tenant_id": effective_tenant,
                    "query": "[" + ",".join(repr(v) for v in vector) + "]",
                    "limit": limit,
                },
            )
            .mappings()
            .all()
        )
    if not products:
        return []
    ids = [row["id"] for row in products]
    order = {pid: idx for idx, pid in enumerate(ids)}
    # Defense-in-depth: re-apply tenant filter on reload
    q2 = db.query(Product).filter(Product.id.in_(ids))
    if effective_tenant is not None:
        q2 = q2.filter(Product.tenant_id == effective_tenant)
    loaded = q2.all()
    loaded.sort(key=lambda p: order[p.id])
    return loaded


@router.get("/", response_model=list[ProductSchema])
def get_products(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    sku: str | None = None,
    category_id: int | None = None,
    tenant_id: int | None = Query(None, description="Tenant filter (superuser only)"),
    response: Response = None,
    current_user: User = Depends(get_current_active_user),
):
    if current_user.is_superuser:
        query = db.query(Product).filter(Product.deleted_at.is_(None))
        if tenant_id is not None:
            query = query.filter(Product.tenant_id == tenant_id)
    else:
        query = db.query(Product).filter(
            Product.tenant_id == current_user.tenant_id, Product.deleted_at.is_(None)
        )
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                func.lower(Product.name).like(like.lower()),
                func.lower(func.coalesce(Product.description, "")).like(like.lower()),
            )
        )
    if sku:
        query = query.filter(Product.sku == sku.strip())
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    limit = min(limit, 200)
    total = query.count()
    products = query.offset(skip).limit(limit).all()
    if response is not None:
        response.headers["X-Total-Count"] = str(total)
    return products


@router.post("/", response_model=ProductSchema)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    tenant_id: int | None = Query(None, description="Tenant filter (superuser only)"),
    current_user: User = Depends(require_permissions("products:manage")),
):
    if current_user.is_superuser:
        effective_tenant = (
            tenant_id if tenant_id is not None else current_user.tenant_id
        )
    else:
        effective_tenant = current_user.tenant_id
    if effective_tenant is None:
        raise HTTPException(
            status_code=400, detail="tenant_id is required for superuser"
        ) from None
    # check category if provided
    if product_in.category_id:
        q = db.query(Category).filter(Category.id == product_in.category_id)
        if current_user.is_superuser:
            # Superuser: category must belong to the target tenant
            q = q.filter(Category.tenant_id == effective_tenant)
        else:
            q = q.filter(Category.tenant_id == current_user.tenant_id)
        category = q.first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    product = Product(**product_in.model_dump(), tenant_id=effective_tenant)
    product.embedding = embed_text(f"{product.name} {product.description or ''}")
    db.add(product)
    db.flush()

    if product.stock_quantity:
        db.add(
            StockMovement(
                product_id=product.id,
                tenant_id=effective_tenant,
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
    tenant_id: int | None = Query(
        None, alias="tenant_id", description="Move to tenant (superuser only)"
    ),
    current_user: User = Depends(require_permissions("products:manage")),
):
    q = db.query(Product).filter(Product.id == product_id)
    if not current_user.is_superuser:
        # Non-superuser cannot move between tenants
        if tenant_id is not None and tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=403,
                detail="Only superuser can move products between tenants",
            ) from None
        q = q.filter(Product.tenant_id == current_user.tenant_id)
    product = q.with_for_update().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_in.model_dump(exclude_unset=True)
    # Handle stock_delta (preferred) vs deprecated stock_quantity absolute
    stock_delta = update_data.pop("stock_delta", None)
    stock_note = update_data.pop("stock_note", None)
    if stock_delta is not None and "stock_quantity" in update_data:
        raise HTTPException(
            status_code=400,
            detail="Provide either stock_delta or stock_quantity, not both",
        ) from None
    if stock_delta is not None:
        if stock_delta == 0:
            raise HTTPException(
                status_code=400, detail="stock_delta cannot be zero"
            ) from None
        new_quantity = product.stock_quantity + stock_delta
        if new_quantity < 0:
            raise HTTPException(
                status_code=400, detail="Stock cannot go below zero"
            ) from None
        # Will be applied after tenant move, before other fields
    # Handle tenant move (superuser only) — must be before other field assignments
    if tenant_id is not None and tenant_id != product.tenant_id:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Only superuser can move products between tenants",
            ) from None
        target_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not target_tenant:
            raise HTTPException(
                status_code=404, detail="Target tenant not found"
            ) from None
        # SKU uniqueness in target tenant (use new sku if provided, else existing)
        sku_to_check = update_data.get("sku", product.sku)
        existing_sku = (
            db.query(Product)
            .filter(Product.tenant_id == tenant_id, Product.sku == sku_to_check)
            .first()
        )
        if existing_sku and existing_sku.id != product.id:
            raise HTTPException(
                status_code=400,
                detail=f"SKU '{sku_to_check}' already exists in target tenant",
            ) from None
        # Category must belong to target tenant (or be cleared)
        if "category_id" in update_data:
            new_category_id = update_data["category_id"]
            if new_category_id is not None:
                cat = (
                    db.query(Category)
                    .filter(
                        Category.id == new_category_id, Category.tenant_id == tenant_id
                    )
                    .first()
                )
                if not cat:
                    raise HTTPException(
                        status_code=400,
                        detail="Category not found in target tenant (or not in same tenant as product)",
                    ) from None
        elif product.category_id is not None:
            # No category update supplied; auto-clear orphaned category
            old_cat = (
                db.query(Category)
                .filter(
                    Category.id == product.category_id, Category.tenant_id == tenant_id
                )
                .first()
            )
            if not old_cat:
                update_data["category_id"] = None
        old_tenant = product.tenant_id
        product.tenant_id = tenant_id
        log_action(
            db=db,
            action="product.tenant_move",
            user_id=current_user.id,
            resource_type="product",
            resource_id=product.id,
            details={"from_tenant": old_tenant, "to_tenant": tenant_id},
        )
    previous_stock_quantity = product.stock_quantity
    # Delta-based adjustment (preferred)
    if stock_delta is not None:
        new_quantity = previous_stock_quantity + stock_delta
        product.stock_quantity = new_quantity
        db.add(
            StockMovement(
                product_id=product.id,
                tenant_id=product.tenant_id,
                user_id=current_user.id,
                movement_type="manual_adjustment",
                quantity_before=previous_stock_quantity,
                quantity_delta=stock_delta,
                quantity_after=new_quantity,
                note=stock_note or "Manual stock adjustment via delta",
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
                "quantity_after": new_quantity,
                "delta": stock_delta,
                "note": stock_note,
            },
        )
        # Remove stock_quantity from update_data handling (already handled)
        # Other fields still need to be applied
    for field, value in update_data.items():
        # Skip stock_quantity if we already handled delta (already popped) — no conflict
        setattr(product, field, value)

    db.add(product)
    embedding_refresh = "name" in update_data or "description" in update_data
    # Legacy absolute path
    stock_changed = "stock_quantity" in update_data and (
        product.stock_quantity != previous_stock_quantity
    )
    # If delta was used, stock already moved, don't re-create manual_adjustment via absolute path
    if stock_delta is not None:
        stock_changed = False
    if embedding_refresh:
        product.embedding = embed_text(f"{product.name} {product.description or ''}")
    if stock_changed:
        db.add(
            StockMovement(
                product_id=product.id,
                tenant_id=product.tenant_id,
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
    q = db.query(Product).filter(Product.id == product_id)
    if not current_user.is_superuser:
        q = q.filter(Product.tenant_id == current_user.tenant_id)
    product = q.first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Use product's tenant for reference checks (superuser case)
    effective_tenant = product.tenant_id
    reference_counts = {
        "order item": db.query(func.count(OrderItem.id))
        .filter(
            OrderItem.product_id == product_id,
            OrderItem.tenant_id == effective_tenant,
        )
        .scalar(),
        "stock movement": db.query(func.count(StockMovement.id))
        .filter(
            StockMovement.product_id == product_id,
            StockMovement.tenant_id == effective_tenant,
        )
        .scalar(),
        "purchase order item": db.query(func.count(PurchaseOrderItem.id))
        .filter(
            PurchaseOrderItem.product_id == product_id,
            PurchaseOrderItem.tenant_id == effective_tenant,
        )
        .scalar(),
        "purchase invoice item": db.query(func.count(PurchaseInvoiceItem.id))
        .filter(
            PurchaseInvoiceItem.product_id == product_id,
            PurchaseInvoiceItem.tenant_id == effective_tenant,
        )
        .scalar(),
        "refund item": db.query(func.count(RefundItem.id))
        .filter(
            RefundItem.product_id == product_id,
            RefundItem.tenant_id == effective_tenant,
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

    old_image_url, old_thumbnail_url = product.image_url, product.thumbnail_url
    product.deleted_at = datetime.now(UTC)
    product.updated_at = datetime.now(UTC)
    db.add(product)
    db.commit()
    delete_media_file(old_image_url)
    delete_media_file(old_thumbnail_url)
    return {"ok": True}


# Image Endpoints


@router.post("/{product_id}/image", response_model=ProductSchema)
def upload_product_image(
    product_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("products:manage")),
):
    """Upload or replace a product photo (jpeg/png/webp, max 5 MB).

    The upload is magic-byte verified, stripped of EXIF, downscaled and
    re-encoded as WebP; a mobile-friendly thumbnail is generated alongside
    it. Both files are stored under ``/media/<tenant_id>/products/``.
    """
    q = db.query(Product).filter(Product.id == product_id)
    if not current_user.is_superuser:
        q = q.filter(Product.tenant_id == current_user.tenant_id)
    product = q.first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    content_type = (file.content_type or "").lower()
    if content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported image type. Allowed: {sorted(_ALLOWED_IMAGE_TYPES)}",
        )

    content = file.file.read(_MAX_IMAGE_BYTES + 1)
    original_bytes, thumbnail_bytes = process_product_image(content)

    file_stem = uuid.uuid4().hex
    original_name = f"{file_stem}_orig.webp"
    thumbnail_name = f"{file_stem}_thumb.webp"
    effective_tenant = product.tenant_id
    tenant_dir = product_media_dir(effective_tenant)
    (tenant_dir / original_name).write_bytes(original_bytes)
    (tenant_dir / thumbnail_name).write_bytes(thumbnail_bytes)

    old_image_url, old_thumbnail_url = product.image_url, product.thumbnail_url
    product.image_url = f"/media/{effective_tenant}/products/{original_name}"
    product.thumbnail_url = f"/media/{effective_tenant}/products/{thumbnail_name}"
    db.add(product)
    try:
        db.commit()
    except Exception:
        (tenant_dir / original_name).unlink(missing_ok=True)
        (tenant_dir / thumbnail_name).unlink(missing_ok=True)
        raise
    db.refresh(product)
    delete_media_file(old_image_url)
    delete_media_file(old_thumbnail_url)
    return product


@router.delete("/{product_id}/image", response_model=ProductSchema)
def delete_product_image(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("products:manage")),
):
    """Remove the product photo and its thumbnail."""
    q = db.query(Product).filter(Product.id == product_id)
    if not current_user.is_superuser:
        q = q.filter(Product.tenant_id == current_user.tenant_id)
    product = q.first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_image_url, old_thumbnail_url = product.image_url, product.thumbnail_url
    product.image_url = None
    product.thumbnail_url = None
    db.add(product)
    db.commit()
    db.refresh(product)
    delete_media_file(old_image_url)
    delete_media_file(old_thumbnail_url)
    return product
