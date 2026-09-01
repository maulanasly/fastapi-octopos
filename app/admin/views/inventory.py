import re
from uuid import uuid4

# pyrefly: ignore [missing-import]
from sqladmin import Flash, action, expose
from sqladmin.filters import (
    AllUniqueStringValuesFilter,
    ForeignKeyFilter,
    OperationColumnFilter,
)
from starlette.exceptions import HTTPException

# pyrefly: ignore [missing-import]
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from app.admin.base import TenantScopedModelView, _selected_tenant_id
from app.admin.color_field import ColorField
from app.admin.formatting import LabeledRelationsMixin
from app.core.audit import log_action
from app.models.product import Category, Product
from app.models.stock_movement import StockMovement
from app.models.tenant import Tenant
from app.services.images import (
    _MAX_IMAGE_BYTES,
    delete_media_file,
    process_product_image,
    product_media_dir,
)


class CategoryAdmin(LabeledRelationsMixin, TenantScopedModelView, model=Category):
    name = "Categories"
    icon = "fa-solid fa-folder-tree"
    category = "Inventory"
    category_icon = "fa-solid fa-boxes-stacked"

    column_list = [
        Category.id,
        Category.name,
        Category.description,
        Category.color,
    ]
    column_searchable_list = [Category.name]
    column_default_sort = [(Category.updated_at, True)]
    form_overrides = {"color": ColorField}
    column_labels = {Category.name: "Category"}
    column_descriptions = {Category.name: "Short category name, searchable"}


class ProductAdmin(LabeledRelationsMixin, TenantScopedModelView, model=Product):
    name = "Products"
    icon = "fa-solid fa-cube"
    category = "Inventory"
    category_icon = "fa-solid fa-boxes-stacked"

    create_template = "product_create.html"
    edit_template = "product_edit.html"

    column_list = [
        Product.id,
        Product.name,
        Product.sku,
        Product.category,
        Product.price,
        Product.stock_quantity,
        Product.reorder_point,
        Product.image_url,
    ]
    column_searchable_list = [Product.name, Product.sku]
    column_sortable_list = [
        Product.price,
        Product.stock_quantity,
        Product.reorder_point,
        Product.lead_time_days,
    ]
    column_default_sort = [(Product.updated_at, True)]
    column_details_list = [
        Product.id,
        Product.name,
        Product.sku,
        Product.category,
        Product.price,
        Product.unit_cost,
        Product.stock_quantity,
        Product.min_stock,
        Product.max_stock,
        Product.reorder_point,
        Product.lead_time_days,
        Product.image_url,
        Product.thumbnail_url,
    ]
    column_filters = [
        ForeignKeyFilter(Product.category_id, Category.name, foreign_model=Category),
        OperationColumnFilter(Product.stock_quantity, title="Stock"),
    ]
    column_labels = {
        Product.name: "Product / SKU",
        Product.category: "Category",
        Product.sku: "SKU",
        Product.price: "Price",
        Product.stock_quantity: "Stock",
    }
    column_descriptions = {
        Product.name: "Full product name, appears on POS tile",
        Product.sku: "Unique per tenant — use Suggest SKU button",
        Product.price: "Selling price (display currency)",
        Product.category: "Optional category for filtering",
    }
    form_args = {
        "name": {"render_kw": {"placeholder": "e.g. Cafe Latte"}},
        "sku": {"render_kw": {"placeholder": "e.g. SKU-CAFE-LATTE"}},
        "price": {"render_kw": {"placeholder": "12.50"}},
    }

    # Stock is ledger-managed via the stock-adjustment action below; never
    # edit it directly through the create/edit forms. Photos go through the
    # upload-image page so files are processed consistently with the API.
    form_excluded_columns = [
        Product.stock_quantity,
        Product.image_url,
        Product.thumbnail_url,
        Product.embedding,  # managed by the embedding service / backfill script
    ]

    @expose("/suggest-sku", methods=["GET"])
    async def suggest_sku(self, request: Request):
        """JSON SKU suggestion for the create/edit form: name-derived,
        uniqueness-checked against the selected tenant's products."""
        name = (request.query_params.get("name") or "").strip()
        exclude_raw = request.query_params.get("exclude_id")
        tenant_id = _selected_tenant_id(request)
        base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:16]
        candidate = f"SKU-{(base or 'product').upper()}"
        db = self.session_maker()
        try:

            def _taken(sku: str) -> bool:
                query = db.query(Product.id).filter(
                    Product.tenant_id == tenant_id, Product.sku == sku
                )
                if exclude_raw and str(exclude_raw).isdigit():
                    query = query.filter(Product.id != int(exclude_raw))
                return query.first() is not None

            original = candidate
            counter = 2
            while _taken(candidate):
                candidate = f"{original}-{counter}"
                counter += 1
        finally:
            db.close()
        return JSONResponse({"sku": candidate})

    @action(
        "adjust-stock",
        label="Record Stock Adjustment",
        confirmation_message=(
            "A StockMovement ledger entry will be recorded. Continue?"
        ),
    )
    async def adjust_stock_action(self, request: Request):
        pk = request.query_params.get("pks", "").split(",")[0]
        return RedirectResponse(
            url=f"/admin/product/adjust-stock?pk={pk}", status_code=303
        )

    @expose("/adjust-stock", methods=["GET", "POST"])
    async def adjust_stock_page(self, request: Request):
        pk = request.query_params.get("pk")
        if not pk:
            raise HTTPException(status_code=404)
        db = self.session_maker()
        try:
            selected_tenant = _selected_tenant_id(request)
            product = (
                db.query(Product)
                .filter(Product.id == int(pk), Product.tenant_id == selected_tenant)
                .first()
            )
            if not product:
                raise HTTPException(status_code=404)

            if request.method == "POST":
                form = await request.form()
                try:
                    delta = int(form.get("delta"))
                except (TypeError, ValueError):
                    Flash.error(
                        request, "Delta must be a whole number.", "Invalid input"
                    )
                    return RedirectResponse(
                        url=f"/admin/product/adjust-stock?pk={pk}", status_code=303
                    )

                note = (form.get("note") or "").strip()
                if delta == 0:
                    Flash.warning(request, "Delta of zero records no movement.")
                    return RedirectResponse(
                        url=f"/admin/product/adjust-stock?pk={pk}", status_code=303
                    )

                quantity_before = product.stock_quantity or 0
                quantity_after = quantity_before + delta
                if quantity_after < 0:
                    Flash.error(
                        request, "Stock cannot go below zero.", "Insufficient stock"
                    )
                    return RedirectResponse(
                        url=f"/admin/product/adjust-stock?pk={pk}", status_code=303
                    )

                product.stock_quantity = quantity_after
                db.add(
                    StockMovement(
                        product_id=product.id,
                        user_id=request.session.get("admin_user_id"),
                        tenant_id=_selected_tenant_id(request),
                        movement_type="manual_adjustment",
                        quantity_before=quantity_before,
                        quantity_delta=delta,
                        quantity_after=quantity_after,
                        note=note or "Manual stock adjustment from admin",
                    )
                )
                log_action(
                    db=db,
                    action="admin.stock_adjust",
                    user_id=request.session.get("admin_user_id"),
                    resource_type="product",
                    resource_id=product.id,
                    details={
                        "quantity_before": quantity_before,
                        "quantity_after": quantity_after,
                        "delta": delta,
                        "note": note,
                    },
                )
                db.commit()
                Flash.success(
                    request,
                    f"Stock adjusted from {quantity_before} to {quantity_after}.",
                )
                return RedirectResponse(
                    url=f"/admin/product/details/{product.id}", status_code=303
                )

            return await self.templates.TemplateResponse(
                request,
                "product_adjust_stock.html",
                context={
                    "product": product,
                    "title": f"Adjust Stock: {product.name}",
                },
            )
        finally:
            db.close()

    @action(
        "upload-image",
        label="Upload Photo",
        confirmation_message=(
            "Replace the product photo. The previous image will be removed."
        ),
    )
    async def upload_image_action(self, request: Request):
        pk = request.query_params.get("pks", "").split(",")[0]
        return RedirectResponse(
            url=f"/admin/product/upload-image?pk={pk}", status_code=303
        )

    @expose("/upload-image", methods=["GET", "POST"])
    async def upload_image_page(self, request: Request):
        pk = request.query_params.get("pk")
        if not pk:
            raise HTTPException(status_code=404)
        db = self.session_maker()
        try:
            selected_tenant = _selected_tenant_id(request)
            product = (
                db.query(Product)
                .filter(Product.id == int(pk), Product.tenant_id == selected_tenant)
                .first()
            )
            if not product:
                raise HTTPException(status_code=404)

            if request.method == "POST":
                form = await request.form()
                upload = form.get("image")
                if upload is None or not getattr(upload, "filename", ""):
                    Flash.error(
                        request, "Choose a jpeg/png/webp image first.", "No file"
                    )
                    return RedirectResponse(
                        url=f"/admin/product/upload-image?pk={pk}", status_code=303
                    )
                content = upload.file.read(_MAX_IMAGE_BYTES + 1)
                try:
                    original_bytes, thumbnail_bytes = process_product_image(content)
                except HTTPException as exc:
                    self._flash_http_error(request, exc)
                    return RedirectResponse(
                        url=f"/admin/product/upload-image?pk={pk}", status_code=303
                    )
                file_stem = uuid4().hex
                original_name = f"{file_stem}_orig.webp"
                thumbnail_name = f"{file_stem}_thumb.webp"
                tenant_dir = product_media_dir(_selected_tenant_id(request))
                (tenant_dir / original_name).write_bytes(original_bytes)
                (tenant_dir / thumbnail_name).write_bytes(thumbnail_bytes)
                old_image_url, old_thumbnail_url = (
                    product.image_url,
                    product.thumbnail_url,
                )
                product.image_url = (
                    f"/media/{_selected_tenant_id(request)}/products/{original_name}"
                )
                product.thumbnail_url = (
                    f"/media/{_selected_tenant_id(request)}/products/{thumbnail_name}"
                )
                db.add(product)
                db.commit()
                delete_media_file(old_image_url)
                delete_media_file(old_thumbnail_url)
                log_action(
                    db=db,
                    action="admin.product_image_upload",
                    user_id=request.session.get("admin_user_id"),
                    resource_type="product",
                    resource_id=product.id,
                )
                db.commit()
                Flash.success(request, "Product photo updated.")
                return RedirectResponse(
                    url=f"/admin/product/details/{product.id}", status_code=303
                )

            return await self.templates.TemplateResponse(
                request,
                "product_upload_image.html",
                context={
                    "product": product,
                    "title": f"Upload Photo: {product.name}",
                },
            )
        finally:
            db.close()

    @action(
        "move-tenant",
        label="Move to Tenant",
        confirmation_message=(
            "Move this product to a different tenant? SKU must be unique in target."
        ),
    )
    async def move_tenant_action(self, request: Request):
        pk = request.query_params.get("pks", "").split(",")[0]
        return RedirectResponse(
            url=f"/admin/product/move-tenant?pk={pk}", status_code=303
        )

    @expose("/move-tenant", methods=["GET", "POST"])
    async def move_tenant_page(self, request: Request):
        pk = request.query_params.get("pk")
        if not pk:
            raise HTTPException(status_code=404)
        db = self.session_maker()
        try:
            product = db.get(Product, int(pk))
            if not product:
                raise HTTPException(status_code=404)
            # Current tenant for display
            current_tenant = db.get(Tenant, product.tenant_id)
            if request.method == "POST":
                form = await request.form()
                raw_target = (form.get("target_tenant_id") or "").strip()
                raw_new_sku = (form.get("new_sku") or "").strip()
                raw_new_cat = (form.get("new_category_id") or "").strip()
                if not raw_target.isdigit():
                    Flash.error(
                        request, "Select a valid target tenant.", "Invalid tenant"
                    )
                    return RedirectResponse(
                        url=f"/admin/product/move-tenant?pk={pk}", status_code=303
                    )
                target_tenant_id = int(raw_target)
                if target_tenant_id == product.tenant_id:
                    Flash.error(request, "Product is already in that tenant.", "No-op")
                    return RedirectResponse(
                        url=f"/admin/product/move-tenant?pk={pk}", status_code=303
                    )
                target_tenant = db.get(Tenant, target_tenant_id)
                if not target_tenant:
                    Flash.error(request, "Target tenant not found.", "Invalid tenant")
                    return RedirectResponse(
                        url=f"/admin/product/move-tenant?pk={pk}", status_code=303
                    )
                # Validate SKU uniqueness in target (use new_sku if provided else existing)
                sku_to_check = raw_new_sku or product.sku
                existing_sku = (
                    db.query(Product)
                    .filter(
                        Product.tenant_id == target_tenant_id,
                        Product.sku == sku_to_check,
                    )
                    .first()
                )
                if existing_sku and existing_sku.id != product.id:
                    Flash.error(
                        request,
                        f"SKU '{sku_to_check}' already exists in target tenant.",
                        "Duplicate SKU",
                    )
                    return RedirectResponse(
                        url=f"/admin/product/move-tenant?pk={pk}", status_code=303
                    )
                # Validate category in target tenant
                new_category_id = None
                if raw_new_cat != "":
                    if not raw_new_cat.isdigit():
                        Flash.error(
                            request, "Category ID must be a number.", "Invalid category"
                        )
                        return RedirectResponse(
                            url=f"/admin/product/move-tenant?pk={pk}", status_code=303
                        )
                    new_category_id = int(raw_new_cat)
                    cat = (
                        db.query(Category)
                        .filter(
                            Category.id == new_category_id,
                            Category.tenant_id == target_tenant_id,
                        )
                        .first()
                    )
                    if not cat:
                        Flash.error(
                            request,
                            "Category not found in target tenant.",
                            "Invalid category",
                        )
                        return RedirectResponse(
                            url=f"/admin/product/move-tenant?pk={pk}", status_code=303
                        )
                else:
                    # No explicit category supplied — auto-clear if current category mismatches
                    if product.category_id is not None:
                        old_cat = (
                            db.query(Category)
                            .filter(
                                Category.id == product.category_id,
                                Category.tenant_id == target_tenant_id,
                            )
                            .first()
                        )
                        if not old_cat:
                            new_category_id = None
                        else:
                            new_category_id = product.category_id
                    else:
                        new_category_id = None

                old_tenant_id = product.tenant_id
                # Apply move
                product.tenant_id = target_tenant_id
                if raw_new_sku:
                    product.sku = raw_new_sku
                product.category_id = new_category_id

                db.add(product)
                log_action(
                    db=db,
                    action="admin.product_tenant_move",
                    user_id=request.session.get("admin_user_id"),
                    resource_type="product",
                    resource_id=product.id,
                    details={
                        "from_tenant": old_tenant_id,
                        "to_tenant": target_tenant_id,
                        "sku": product.sku,
                    },
                )
                db.commit()
                Flash.success(
                    request,
                    f"Product moved from tenant {old_tenant_id} to {target_tenant_id}.",
                )
                return RedirectResponse(
                    url=f"/admin/product/details/{product.id}", status_code=303
                )

            # GET — render form
            tenants = db.query(Tenant).order_by(Tenant.id.asc()).all()
            return await self.templates.TemplateResponse(
                request,
                "product_move_tenant.html",
                context={
                    "product": product,
                    "current_tenant": current_tenant,
                    "tenants": tenants,
                },
            )
        finally:
            db.close()


class StockMovementAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=StockMovement
):
    name = "Stock Movements"
    icon = "fa-solid fa-arrows-left-right-to-line"
    category = "Inventory"
    category_icon = "fa-solid fa-boxes-stacked"

    column_list = [
        StockMovement.id,
        StockMovement.product,
        StockMovement.user,
        StockMovement.movement_type,
        StockMovement.quantity_before,
        StockMovement.quantity_delta,
        StockMovement.quantity_after,
        StockMovement.order_id,
        StockMovement.refund_id,
        StockMovement.created_at,
    ]
    column_searchable_list = [StockMovement.movement_type, StockMovement.note]
    column_sortable_list = [StockMovement.created_at, StockMovement.id]
    column_default_sort = [(StockMovement.created_at, True)]
    column_filters = [
        AllUniqueStringValuesFilter(StockMovement.movement_type, title="Movement Type"),
        # Huge product list: use ID input instead of dropdown (avoids loading 10k options)
        OperationColumnFilter(StockMovement.product_id, title="Product ID"),
    ]
    column_labels = {
        StockMovement.movement_type: "Movement Type",
        StockMovement.product: "Product",
    }
    can_create = False
    can_edit = False
    can_delete = False
