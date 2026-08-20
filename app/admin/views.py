import re
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

# pyrefly: ignore [missing-import]
from sqladmin import BaseView, Flash, ModelView, action, expose
from sqladmin.filters import AllUniqueStringValuesFilter, ForeignKeyFilter
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from starlette.exceptions import HTTPException

# pyrefly: ignore [missing-import]
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from wtforms import SelectField

from app.admin.color_field import ColorField
from app.admin.formatting import LabeledRelationsMixin, _make_relation_formatter
from app.admin.password_field import AdminPasswordField
from app.core.audit import log_action
from app.core.database import SessionLocal
from app.core.localization import (
    SUPPORTED_COUNTRY_CODES,
    SUPPORTED_CURRENCIES,
    SUPPORTED_DATE_FORMATS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_NUMBER_FORMATS,
    SUPPORTED_TIMEZONES,
    format_currency,
    get_localization_setting,
)
from app.core.security import get_password_hash
from app.models.customer import Customer, LoyaltyTransaction
from app.models.drawer import DrawerSession
from app.models.localization import LocalizationSetting
from app.models.order import Order, OrderItem
from app.models.product import Category, Product
from app.models.promotion import Promotion
from app.models.purchase import (
    PurchaseInvoice,
    PurchaseInvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
    SupplierPayment,
)
from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.models.refund import Refund, RefundItem
from app.models.shift_reconciliation import ShiftReconciliation
from app.models.stock_movement import StockMovement
from app.models.sync_event import SyncEventLog
from app.models.tax import OrderTaxLine, TaxRule
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.drawer import ShiftReconciliationCreate
from app.schemas.purchase import (
    PurchaseInvoiceCreate,
    PurchaseInvoiceItemCreate,
    PurchaseInvoiceReviewAction,
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    PurchaseOrderReceive,
    PurchaseOrderReceiveItem,
    PurchaseOrderReviewAction,
    SupplierPaymentReviewAction,
)
from app.schemas.refund import RefundCreate, RefundItemCreate
from app.services.auto_po import auto_generate_purchase_orders
from app.services.drawers import build_reconciliation, compute_drawer_totals
from app.services.images import (
    _MAX_IMAGE_BYTES,
    delete_media_file,
    process_product_image,
    product_media_dir,
)
from app.services.purchasing import (
    approve_purchase_invoice,
    approve_supplier_payment,
    create_purchase_invoice,
    create_purchase_order,
    mark_purchase_order_ordered,
    receive_purchase_order_items,
    reject_purchase_invoice,
    reject_supplier_payment,
    submit_purchase_invoice_for_review,
    submit_purchase_order_for_review,
)
from app.services.refunds import create_refund
from app.services.reports import (
    get_category_sales_data,
    get_executive_summary_data,
    get_invoice_summary_data,
    get_low_stock_products_data,
    get_sales_summary_data,
    get_supplier_payment_summary_data,
    get_top_customers_data,
    get_top_products_data,
)

REPORTS_CACHE_SECONDS = 120
_reports_cache: dict[tuple[str, str, str], tuple[float, dict]] = {}

# The admin panel is superuser-only (cross-tenant by design). The superuser
# picks a working tenant via the Tenant switcher; rows the panel creates that
# require a tenant land in that tenant (default: the seeded default tenant).
ADMIN_TENANT_ID = 1


def _selected_tenant_id(request: Request) -> int:
    """The tenant selected by the superuser in the panel (default tenant 1)."""
    return int(request.session.get("admin_tenant_id") or ADMIN_TENANT_ID)


def _unique_tenant_slug(db, name: str, current_id: int | None = None) -> str:
    """Unique slug for a tenant name, mirroring app.services.tenants."""
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40]
    base = base or "business"
    slug = base
    counter = 1
    while True:
        query = db.query(Tenant.id).filter(Tenant.slug == slug)
        if current_id is not None:
            query = query.filter(Tenant.id != current_id)
        if not query.first():
            return slug
        counter += 1
        slug = f"{base}-{counter}"


class TenantScopedModelView(ModelView):
    """ModelView that stamps tenant_id on rows created through the panel.

    Also surfaces the tenant on every tenant-scoped list: the tenant column
    (rendered as the tenant name, right after ``id``) and a tenant filter
    dropdown. Detail pages already render all relationships labeled via
    :class:`LabeledRelationsMixin`.
    """

    #: Keep the ``tenant`` relationship out of create/edit forms: writes are
    #: scoped to the Tenant switcher (stamped in ``on_model_change``), and an
    #: unset dropdown would otherwise overwrite the stamp with NULL. Views
    #: that manage tenant explicitly in their form opt out.
    exclude_tenant_from_form = True

    def __init__(self, *args, **kwargs):
        model = getattr(self, "model", None)
        tenant_rel = getattr(model, "tenant", None) if model is not None else None
        # Exclude tenant from the form BEFORE ModelView.__init__ snapshots
        # _form_prop_names; a blank tenant dropdown would otherwise overwrite
        # the stamped tenant_id with NULL on create/edit.
        if tenant_rel is not None and self.exclude_tenant_from_form:
            excluded = list(getattr(self, "form_excluded_columns", []) or [])
            excluded_keys = {getattr(item, "key", item) for item in excluded}
            if "tenant" not in excluded_keys:
                self.form_excluded_columns = excluded + [tenant_rel]
        super().__init__(*args, **kwargs)
        if model is None or tenant_rel is None:
            return
        columns = list(getattr(self, "column_list", []) or [])
        if not any(getattr(column, "key", None) == "tenant" for column in columns):
            self.column_list = columns[:1] + [tenant_rel] + columns[1:]
            # LabeledRelationsMixin built its formatters from the pre-injection
            # column_list, so label the injected tenant column here.
            self.column_formatters = {
                **dict(getattr(self, "column_formatters", {}) or {}),
                tenant_rel: _make_relation_formatter("tenant"),
            }
        filters = list(getattr(self, "column_filters", []) or [])
        if not any(
            getattr(filter_, "parameter_name", None) == "tenant_id"
            for filter_ in filters
        ):
            self.column_filters = [
                ForeignKeyFilter(model.tenant_id, Tenant.name, foreign_model=Tenant),
                *filters,
            ]

    async def on_model_change(
        self, data: dict, model: Any, is_created: bool, request: Request
    ) -> None:
        if is_created and hasattr(model, "tenant_id"):
            if "tenant_id" in model.__table__.c and model.tenant_id is None:
                model.tenant_id = _selected_tenant_id(request)
        await super().on_model_change(data, model, is_created, request)


class TenantAdmin(ModelView, model=Tenant):
    """Platform-level tenant registry (create, toggle active)."""

    name = "Tenants"
    icon = "fa-solid fa-building"
    category = "Platform"
    category_icon = "fa-solid fa-globe"

    column_list = [
        Tenant.id,
        Tenant.name,
        Tenant.slug,
        Tenant.is_active,
        Tenant.created_at,
    ]
    column_searchable_list = [Tenant.name, Tenant.slug]
    form_columns = [Tenant.name, Tenant.slug, Tenant.is_active]
    # A blank slug is allowed in the form: it is auto-generated from the name
    # (or uniquified) in on_model_change. Tenant.slug carries a client-side
    # default so sqladmin does not scaffold InputRequired on it.
    column_default_sort = [(Tenant.id, True)]

    async def on_model_change(
        self, data: dict, model: Any, is_created: bool, request: Request
    ) -> None:
        # sqladmin applies form fields to the model AFTER on_model_change,
        # so read/mutate the pending values from ``data``.
        db = SessionLocal()
        try:
            raw = (data.get("slug") or "").strip()
            if not raw:
                raw = data.get("name") or "Business"
            data["slug"] = _unique_tenant_slug(
                db, raw, current_id=None if is_created else model.id
            )
        finally:
            db.close()
        await super().on_model_change(data, model, is_created, request)


class TenantSwitchAdmin(BaseView):
    """Superuser tenant selector scoping panel writes and workflow/report
    queries to a chosen tenant (default: the seeded default tenant)."""

    name = "Tenant"
    icon = "fa-solid fa-building-circle-arrow-right"
    category = "Platform"

    @expose("/tenant", methods=["GET", "POST"])
    async def tenant_switch(self, request: Request):
        if request.method == "POST":
            form = await request.form()
            raw = form.get("tenant_id")
            if str(raw).isdigit():
                request.session["admin_tenant_id"] = int(raw)
                return RedirectResponse(url="/admin/tenant", status_code=303)
        db = SessionLocal()
        try:
            tenants = db.query(Tenant).order_by(Tenant.id.asc()).all()
            current_tenant_id = _selected_tenant_id(request)
        finally:
            db.close()
        return await self.templates.TemplateResponse(
            request,
            "tenant_switch.html",
            context={
                "tenants": tenants,
                "current_tenant_id": current_tenant_id,
            },
        )


class UserAdmin(LabeledRelationsMixin, TenantScopedModelView, model=User):
    name = "Users"
    icon = "fa-solid fa-user"
    category = "Access Control"
    category_icon = "fa-solid fa-user-shield"

    column_list = [
        User.id,
        User.email,
        User.full_name,
        User.is_active,
        User.is_superuser,
        User.roles,
    ]
    column_searchable_list = [User.email, User.full_name]
    can_delete = False

    column_labels = {User.hashed_password: "Password"}
    column_default_sort = [(User.id, True)]
    form_overrides = {User.hashed_password: AdminPasswordField}

    async def on_model_change(
        self, data: dict, model: User, is_created: bool, request: Request
    ) -> None:
        """Hash the typed password; never persist a raw string.

        sqladmin calls this before applying the form values to the model,
        so mutating ``data`` here is authoritative. A blank submission
        keeps the existing hash on edits and leaves ``None`` on creates
        (Google-only users).
        """
        submitted = (data.get("hashed_password") or "").strip()
        if submitted:
            data["hashed_password"] = get_password_hash(submitted)
        elif is_created:
            data.pop("hashed_password", None)
        else:
            # Preserve the current hash (form value is blank).
            data.pop("hashed_password", None)
        await super().on_model_change(data, model, is_created, request)


class LocalizationSettingAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=LocalizationSetting
):
    name = "Localization"
    icon = "fa-solid fa-earth-asia"
    category = "System"
    category_icon = "fa-solid fa-gear"

    # The tenant is chosen explicitly in the create/edit form (singleton
    # per tenant semantics are enforced in on_model_change).
    exclude_tenant_from_form = False

    column_list = [
        LocalizationSetting.id,
        LocalizationSetting.tenant,
        LocalizationSetting.language,
        LocalizationSetting.timezone,
        LocalizationSetting.currency,
        LocalizationSetting.date_format,
        LocalizationSetting.number_format,
        LocalizationSetting.country_code,
        LocalizationSetting.updated_at,
    ]
    column_default_sort = [(LocalizationSetting.updated_at, True)]
    can_delete = False

    form_columns = [
        LocalizationSetting.tenant,
        LocalizationSetting.language,
        LocalizationSetting.timezone,
        LocalizationSetting.currency,
        LocalizationSetting.date_format,
        LocalizationSetting.number_format,
        LocalizationSetting.country_code,
    ]

    # Render supported values as selects instead of free-text inputs. The
    # choices come from the same constants served by GET /localization/options.
    form_overrides = {
        LocalizationSetting.language: SelectField,
        LocalizationSetting.timezone: SelectField,
        LocalizationSetting.currency: SelectField,
        LocalizationSetting.date_format: SelectField,
        LocalizationSetting.number_format: SelectField,
        LocalizationSetting.country_code: SelectField,
    }
    form_args = {
        "language": {
            "choices": SUPPORTED_LANGUAGES,
            "validate_choice": False,
        },
        "timezone": {
            "choices": SUPPORTED_TIMEZONES,
            "validate_choice": False,
        },
        "currency": {
            "choices": SUPPORTED_CURRENCIES,
            "validate_choice": False,
        },
        "date_format": {
            "choices": SUPPORTED_DATE_FORMATS,
            "validate_choice": False,
        },
        "number_format": {
            "choices": SUPPORTED_NUMBER_FORMATS,
            "validate_choice": False,
        },
        "country_code": {
            "choices": SUPPORTED_COUNTRY_CODES,
            "validate_choice": False,
        },
    }

    async def on_model_change(
        self, data: dict, model: Any, is_created: bool, request: Request
    ) -> None:
        """Keep one LocalizationSetting per tenant (singleton semantics the
        API relies on): reject creating a second row for the chosen tenant,
        or moving an existing row onto a tenant that already has one."""
        chosen = data.get("tenant")
        try:
            tenant_id = int(chosen)
        except (TypeError, ValueError):
            tenant_id = _selected_tenant_id(request)
        db = SessionLocal()
        try:
            existing = (
                db.query(LocalizationSetting)
                .filter(LocalizationSetting.tenant_id == tenant_id)
                .first()
            )
        finally:
            db.close()
        if existing and (is_created or existing.id != model.id):
            raise ValueError(
                "Localization already exists for the chosen tenant; "
                "edit the existing row instead."
            )
        if is_created:
            data["tenant"] = tenant_id
        await super().on_model_change(data, model, is_created, request)


class RoleAdmin(LabeledRelationsMixin, ModelView, model=Role):
    name = "Roles"
    icon = "fa-solid fa-id-badge"
    category = "Access Control"
    category_icon = "fa-solid fa-user-shield"

    column_list = [
        Role.id,
        Role.name,
        Role.description,
        Role.is_system,
        Role.permissions,
    ]
    # To-many relationships are only rendered in the detail view (sqladmin
    # list view skips them); explicit column_details_list keeps the mixin's
    # formatters active so codes render instead of object reprs.
    column_details_list = [
        Role.id,
        Role.name,
        Role.description,
        Role.is_system,
        Role.permissions,
    ]
    column_searchable_list = [Role.name, Role.description]
    column_sortable_list = [Role.id, Role.name]
    column_default_sort = [(Role.id, True)]

    async def check_can_edit(self, request: Request, model: Role) -> bool:
        if getattr(model, "is_system", False):
            return False
        return True

    async def check_can_delete(self, request: Request, model: Role) -> bool:
        if getattr(model, "is_system", False):
            return False
        return True


class PermissionAdmin(LabeledRelationsMixin, ModelView, model=Permission):
    name = "Permissions"
    icon = "fa-solid fa-key"
    category = "Access Control"
    category_icon = "fa-solid fa-user-shield"

    column_list = [
        Permission.id,
        Permission.code,
        Permission.description,
        Permission.roles,
    ]
    column_searchable_list = [Permission.code, Permission.description]
    column_sortable_list = [Permission.id, Permission.code]
    column_default_sort = [(Permission.id, True)]


class UserRoleAdmin(LabeledRelationsMixin, ModelView, model=UserRole):
    name = "User Roles"
    icon = "fa-solid fa-user-tag"
    category = "Access Control"
    category_icon = "fa-solid fa-user-shield"

    column_list = [UserRole.id, UserRole.user_id, UserRole.role_id]
    column_sortable_list = [UserRole.id, UserRole.user_id, UserRole.role_id]
    column_default_sort = [(UserRole.id, True)]
    can_create = False
    can_edit = False
    can_delete = False


class RolePermissionAdmin(LabeledRelationsMixin, ModelView, model=RolePermission):
    name = "Role Permissions"
    icon = "fa-solid fa-user-lock"
    category = "Access Control"
    category_icon = "fa-solid fa-user-shield"

    column_list = [
        RolePermission.id,
        RolePermission.role_id,
        RolePermission.permission_id,
    ]
    column_sortable_list = [
        RolePermission.id,
        RolePermission.role_id,
        RolePermission.permission_id,
    ]
    column_default_sort = [(RolePermission.id, True)]
    can_create = False
    can_edit = False
    can_delete = False


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
        Product.price,
        Product.unit_cost,
        Product.stock_quantity,
        Product.min_stock,
        Product.max_stock,
        Product.reorder_point,
        Product.lead_time_days,
        Product.category,
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
            product = db.get(Product, int(pk))
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
            product = db.get(Product, int(pk))
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


class PromotionAdmin(LabeledRelationsMixin, TenantScopedModelView, model=Promotion):
    name = "Promotions"
    icon = "fa-solid fa-tags"
    category = "Marketing"
    category_icon = "fa-solid fa-bullhorn"

    column_list = [
        Promotion.id,
        Promotion.code,
        Promotion.name,
        Promotion.discount_type,
        Promotion.discount_value,
        Promotion.applies_to,
        Promotion.is_active,
        Promotion.usage_count,
        Promotion.usage_limit,
        Promotion.starts_at,
        Promotion.ends_at,
    ]
    column_searchable_list = [Promotion.code, Promotion.name, Promotion.description]
    column_sortable_list = [Promotion.id, Promotion.usage_count, Promotion.starts_at]
    column_default_sort = [(Promotion.created_at, True)]


class CustomerAdmin(LabeledRelationsMixin, TenantScopedModelView, model=Customer):
    name = "Customers"
    icon = "fa-solid fa-user-group"
    category = "Customers"
    category_icon = "fa-solid fa-user-group"

    column_list = [
        Customer.id,
        Customer.name,
        Customer.email,
        Customer.phone,
        Customer.points_balance,
        Customer.is_active,
        Customer.created_at,
    ]
    column_searchable_list = [Customer.name, Customer.email, Customer.phone]
    column_sortable_list = [Customer.id, Customer.points_balance, Customer.created_at]
    column_default_sort = [(Customer.created_at, True)]


class LoyaltyTransactionAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=LoyaltyTransaction
):
    name = "Loyalty Transactions"
    icon = "fa-solid fa-star"
    category = "Customers"
    category_icon = "fa-solid fa-user-group"

    column_list = [
        LoyaltyTransaction.id,
        LoyaltyTransaction.customer,
        LoyaltyTransaction.order_id,
        LoyaltyTransaction.transaction_type,
        LoyaltyTransaction.points_delta,
        LoyaltyTransaction.balance_after,
        LoyaltyTransaction.created_at,
    ]
    column_searchable_list = [
        LoyaltyTransaction.transaction_type,
        LoyaltyTransaction.note,
    ]
    column_sortable_list = [LoyaltyTransaction.id, LoyaltyTransaction.created_at]
    column_default_sort = [(LoyaltyTransaction.created_at, True)]
    can_create = False
    can_edit = False
    can_delete = False


class SupplierAdmin(LabeledRelationsMixin, TenantScopedModelView, model=Supplier):
    name = "Suppliers"
    icon = "fa-solid fa-truck-field"
    category = "Purchasing"
    category_icon = "fa-solid fa-truck"

    column_list = [
        Supplier.id,
        Supplier.name,
        Supplier.contact_email,
        Supplier.phone,
        Supplier.is_active,
        Supplier.created_at,
    ]
    column_searchable_list = [Supplier.name, Supplier.contact_email, Supplier.phone]
    column_sortable_list = [Supplier.created_at, Supplier.id]
    column_default_sort = [(Supplier.created_at, True)]


class PurchaseOrderAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=PurchaseOrder
):
    name = "Purchase Orders"
    icon = "fa-solid fa-file-invoice"
    category = "Purchasing"
    category_icon = "fa-solid fa-truck"

    column_list = [
        PurchaseOrder.id,
        PurchaseOrder.supplier,
        PurchaseOrder.user,
        PurchaseOrder.status,
        PurchaseOrder.total_estimated_amount,
        PurchaseOrder.created_at,
        PurchaseOrder.ordered_at,
        PurchaseOrder.received_at,
    ]
    column_searchable_list = [PurchaseOrder.status]
    column_sortable_list = [PurchaseOrder.created_at, PurchaseOrder.received_at]
    column_default_sort = [(PurchaseOrder.created_at, True)]
    can_create = False
    can_edit = False
    can_delete = False


class PurchaseOrderItemAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=PurchaseOrderItem
):
    name = "PO Items"
    icon = "fa-solid fa-list-check"
    category = "Purchasing"
    category_icon = "fa-solid fa-truck"

    column_list = [
        PurchaseOrderItem.id,
        PurchaseOrderItem.purchase_order_id,
        PurchaseOrderItem.product,
        PurchaseOrderItem.quantity_ordered,
        PurchaseOrderItem.quantity_received,
        PurchaseOrderItem.unit_cost,
    ]
    column_searchable_list = [PurchaseOrderItem.purchase_order_id]
    column_sortable_list = [PurchaseOrderItem.id]
    column_default_sort = [(PurchaseOrderItem.id, True)]
    can_create = False
    can_edit = False
    can_delete = False


class PurchaseInvoiceAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=PurchaseInvoice
):
    name = "Purchase Invoices"
    icon = "fa-solid fa-file-invoice-dollar"
    category = "Purchasing"
    category_icon = "fa-solid fa-truck"

    column_list = [
        PurchaseInvoice.id,
        PurchaseInvoice.invoice_number,
        PurchaseInvoice.supplier,
        PurchaseInvoice.purchase_order,
        PurchaseInvoice.user,
        PurchaseInvoice.status,
        PurchaseInvoice.total_amount,
        PurchaseInvoice.variance_amount,
        PurchaseInvoice.has_quantity_variance,
        PurchaseInvoice.has_price_variance,
        PurchaseInvoice.created_at,
    ]
    column_searchable_list = [PurchaseInvoice.invoice_number, PurchaseInvoice.status]
    column_sortable_list = [
        PurchaseInvoice.created_at,
        PurchaseInvoice.total_amount,
        PurchaseInvoice.variance_amount,
    ]
    column_default_sort = [(PurchaseInvoice.created_at, True)]
    can_create = False
    can_edit = False
    can_delete = False


class PurchaseInvoiceItemAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=PurchaseInvoiceItem
):
    name = "Invoice Items"
    icon = "fa-solid fa-receipt"
    category = "Purchasing"
    category_icon = "fa-solid fa-truck"

    column_list = [
        PurchaseInvoiceItem.id,
        PurchaseInvoiceItem.invoice_id,
        PurchaseInvoiceItem.purchase_order_item_id,
        PurchaseInvoiceItem.product,
        PurchaseInvoiceItem.billed_quantity,
        PurchaseInvoiceItem.billed_unit_cost,
        PurchaseInvoiceItem.expected_quantity,
        PurchaseInvoiceItem.expected_unit_cost,
        PurchaseInvoiceItem.quantity_variance,
        PurchaseInvoiceItem.price_variance,
        PurchaseInvoiceItem.line_total,
    ]
    column_searchable_list = [
        PurchaseInvoiceItem.invoice_id,
        PurchaseInvoiceItem.purchase_order_item_id,
    ]
    column_sortable_list = [PurchaseInvoiceItem.id, PurchaseInvoiceItem.line_total]
    column_default_sort = [(PurchaseInvoiceItem.id, True)]
    can_create = False
    can_edit = False
    can_delete = False


class SupplierPaymentAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=SupplierPayment
):
    name = "Supplier Payments"
    icon = "fa-solid fa-money-bill-transfer"
    category = "Purchasing"
    category_icon = "fa-solid fa-truck"

    column_list = [
        SupplierPayment.id,
        SupplierPayment.supplier,
        SupplierPayment.invoice,
        SupplierPayment.user,
        SupplierPayment.amount,
        SupplierPayment.payment_method,
        SupplierPayment.status,
        SupplierPayment.payment_date,
        SupplierPayment.reference,
        SupplierPayment.created_at,
    ]
    column_searchable_list = [
        SupplierPayment.status,
        SupplierPayment.payment_method,
        SupplierPayment.reference,
    ]
    column_sortable_list = [
        SupplierPayment.created_at,
        SupplierPayment.amount,
        SupplierPayment.status,
    ]
    column_default_sort = [(SupplierPayment.created_at, True)]
    can_create = False
    can_edit = False
    can_delete = False


class OrderAdmin(LabeledRelationsMixin, TenantScopedModelView, model=Order):
    name = "Orders"
    icon = "fa-solid fa-cart-shopping"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

    column_list = [
        Order.id,
        Order.user,
        Order.customer,
        Order.status,
        Order.promotion,
        Order.grand_total_amount,
        Order.paid_amount,
        Order.remaining_amount,
        Order.created_at,
    ]
    column_details_list = [
        Order.id,
        Order.user,
        Order.customer,
        Order.promotion,
        Order.subtotal_amount,
        Order.discount_amount,
        Order.taxable_base_amount,
        Order.tax_total_amount,
        Order.grand_total_amount,
        Order.redeemed_points,
        Order.total_amount,
        Order.paid_amount,
        Order.change_amount,
        Order.remaining_amount,
        Order.status,
        Order.reservation_status,
        Order.reservation_expires_at,
        Order.created_at,
    ]
    column_sortable_list = [Order.created_at, Order.total_amount]
    column_searchable_list = [Order.id]
    column_default_sort = [(Order.created_at, True)]
    can_create = False
    can_edit = False
    can_delete = False


class OrderItemAdmin(LabeledRelationsMixin, TenantScopedModelView, model=OrderItem):
    name = "Order Items"
    icon = "fa-solid fa-basket-shopping"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

    column_list = [
        OrderItem.id,
        OrderItem.order_id,
        OrderItem.product,
        OrderItem.quantity,
        OrderItem.unit_price,
    ]
    column_searchable_list = [OrderItem.order_id]
    column_default_sort = [(OrderItem.id, True)]
    can_create = False
    can_edit = False
    can_delete = False


class DrawerSessionAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=DrawerSession
):
    name = "Drawer Sessions"
    icon = "fa-solid fa-cash-register"
    category = "Operations"
    category_icon = "fa-solid fa-screwdriver-wrench"

    column_list = [
        DrawerSession.id,
        DrawerSession.user,
        DrawerSession.opened_at,
        DrawerSession.closed_at,
        DrawerSession.starting_cash,
        DrawerSession.ending_cash,
        DrawerSession.status,
    ]
    column_filters = [
        AllUniqueStringValuesFilter(DrawerSession.status),
        ForeignKeyFilter(DrawerSession.user_id, User.email, foreign_model=User),
    ]
    column_searchable_list = [DrawerSession.status]
    column_sortable_list = [DrawerSession.opened_at, DrawerSession.closed_at]
    column_default_sort = [(DrawerSession.opened_at, True)]
    can_create = False
    can_edit = False
    can_delete = False


class ShiftReconciliationAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=ShiftReconciliation
):
    name = "Shift Reconciliations"
    icon = "fa-solid fa-calculator"
    category = "Operations"
    category_icon = "fa-solid fa-screwdriver-wrench"

    column_list = [
        ShiftReconciliation.id,
        ShiftReconciliation.drawer_session_id,
        ShiftReconciliation.closed_by_user,
        ShiftReconciliation.expected_cash,
        ShiftReconciliation.counted_cash,
        ShiftReconciliation.cash_variance,
        ShiftReconciliation.expected_non_cash,
        ShiftReconciliation.counted_non_cash,
        ShiftReconciliation.non_cash_variance,
        ShiftReconciliation.created_at,
    ]
    column_searchable_list = [ShiftReconciliation.drawer_session_id]
    column_sortable_list = [ShiftReconciliation.created_at, ShiftReconciliation.id]
    column_default_sort = [(ShiftReconciliation.created_at, True)]
    can_create = False
    can_edit = False
    can_delete = False


class RefundAdmin(LabeledRelationsMixin, TenantScopedModelView, model=Refund):
    name = "Refunds"
    icon = "fa-solid fa-rotate-left"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

    column_list = [
        Refund.id,
        Refund.order_id,
        Refund.user,
        Refund.total_amount,
        Refund.created_at,
    ]
    column_searchable_list = [Refund.order_id]
    column_sortable_list = [Refund.created_at, Refund.total_amount]
    column_default_sort = [(Refund.created_at, True)]
    can_create = False
    can_edit = False
    can_delete = False


class RefundItemAdmin(LabeledRelationsMixin, TenantScopedModelView, model=RefundItem):
    name = "Refund Items"
    icon = "fa-solid fa-rotate"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

    column_list = [
        RefundItem.id,
        RefundItem.refund_id,
        RefundItem.order_item_id,
        RefundItem.product,
        RefundItem.quantity,
        RefundItem.unit_price,
    ]
    column_searchable_list = [RefundItem.refund_id, RefundItem.order_item_id]
    column_default_sort = [(RefundItem.id, True)]
    can_create = False
    can_edit = False
    can_delete = False


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
    can_create = False
    can_edit = False
    can_delete = False


class SyncEventLogAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=SyncEventLog
):
    name = "Sync Events"
    icon = "fa-solid fa-arrows-rotate"
    category = "System"
    category_icon = "fa-solid fa-gear"

    column_list = [
        SyncEventLog.id,
        SyncEventLog.user,
        SyncEventLog.client_event_id,
        SyncEventLog.event_type,
        SyncEventLog.idempotency_key,
        SyncEventLog.status,
        SyncEventLog.resource_type,
        SyncEventLog.resource_id,
        SyncEventLog.processed_at,
    ]
    column_searchable_list = [
        SyncEventLog.client_event_id,
        SyncEventLog.event_type,
        SyncEventLog.idempotency_key,
        SyncEventLog.status,
    ]
    column_sortable_list = [SyncEventLog.processed_at, SyncEventLog.id]
    column_default_sort = [(SyncEventLog.processed_at, True)]
    can_create = False
    can_edit = False
    can_delete = False


class TaxRuleAdmin(LabeledRelationsMixin, TenantScopedModelView, model=TaxRule):
    name = "Tax Rules"
    icon = "fa-solid fa-percent"
    category = "Marketing"
    category_icon = "fa-solid fa-bullhorn"

    column_list = [
        TaxRule.id,
        TaxRule.name,
        TaxRule.tax_scope,
        TaxRule.tax_mode,
        TaxRule.rate,
        TaxRule.product,
        TaxRule.category,
        TaxRule.starts_at,
        TaxRule.ends_at,
        TaxRule.is_active,
        TaxRule.updated_at,
    ]
    column_searchable_list = [TaxRule.name, TaxRule.description]
    column_sortable_list = [TaxRule.id, TaxRule.rate, TaxRule.updated_at]
    column_default_sort = [(TaxRule.updated_at, True)]


class OrderTaxLineAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=OrderTaxLine
):
    name = "Order Tax Lines"
    icon = "fa-solid fa-receipt"
    category = "Sales"
    category_icon = "fa-solid fa-cart-shopping"

    column_list = [
        OrderTaxLine.id,
        OrderTaxLine.order_id,
        OrderTaxLine.tax_rule,
        OrderTaxLine.tax_name,
        OrderTaxLine.tax_scope,
        OrderTaxLine.tax_mode,
        OrderTaxLine.tax_rate,
        OrderTaxLine.taxable_base,
        OrderTaxLine.tax_amount,
        OrderTaxLine.applied_at,
    ]
    column_searchable_list = [OrderTaxLine.tax_name, OrderTaxLine.tax_scope]
    column_sortable_list = [OrderTaxLine.applied_at, OrderTaxLine.id]
    column_default_sort = [(OrderTaxLine.applied_at, True)]
    can_create = False
    can_edit = False
    can_delete = False


class ReportsAdmin(BaseView):
    name = "Reports Dashboard"
    icon = "fa-solid fa-chart-line"
    category = "Reports"
    category_icon = "fa-solid fa-chart-pie"

    def _period_range(self, now: datetime, period: str) -> tuple:
        if period == "today":
            start_date = datetime(
                year=now.year,
                month=now.month,
                day=now.day,
                tzinfo=UTC,
            )
        elif period == "7d":
            start_date = now - timedelta(days=7)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        elif period == "month":
            start_date = datetime(
                year=now.year,
                month=now.month,
                day=1,
                tzinfo=UTC,
            )
        else:
            start_date = None
        return start_date, None

    def _build_report_data(self, db, period: str, localization) -> dict:
        now = datetime.now(UTC)
        if period not in ("today", "7d", "30d", "month"):
            period = "all"
        start_date, end_date = self._period_range(now, period)

        sales_summary = get_sales_summary_data(
            db=db, start_date=start_date, end_date=end_date
        )
        top_products = get_top_products_data(
            db=db, start_date=start_date, end_date=end_date, limit=10
        )
        category_sales = get_category_sales_data(
            db=db, start_date=start_date, end_date=end_date
        )
        low_stock_products = get_low_stock_products_data(db=db)
        top_customers = get_top_customers_data(
            db=db, start_date=start_date, end_date=end_date, limit=5
        )
        invoice_summary = get_invoice_summary_data(
            db=db, start_date=start_date, end_date=end_date
        )
        payment_summary = get_supplier_payment_summary_data(
            db=db, start_date=start_date, end_date=end_date
        )
        executive_summary = get_executive_summary_data(
            db=db, invoice_summary=invoice_summary
        )

        localized = {
            "net_revenue": format_currency(
                float(sales_summary["net_revenue"]),
                localization.currency,
                localization.number_format,
            ),
            "total_refunds": format_currency(
                float(sales_summary["total_refunds"]),
                localization.currency,
                localization.number_format,
            ),
            "average_order_value": format_currency(
                float(sales_summary["average_order_value"]),
                localization.currency,
                localization.number_format,
            ),
            "gross_revenue": format_currency(
                float(sales_summary["gross_revenue"]),
                localization.currency,
                localization.number_format,
            ),
            "total_discounts": format_currency(
                float(sales_summary["total_discounts"]),
                localization.currency,
                localization.number_format,
            ),
            "purchase_received_value": format_currency(
                float(executive_summary["purchase_received_value"]),
                localization.currency,
                localization.number_format,
            ),
            "average_cash_variance": format_currency(
                float(executive_summary["average_cash_variance"]),
                localization.currency,
                localization.number_format,
            ),
            "invoice_approved_total": format_currency(
                float(executive_summary["invoice_approved_total"]),
                localization.currency,
                localization.number_format,
            ),
            "invoice_variance_total": format_currency(
                float(executive_summary["invoice_variance_total"]),
                localization.currency,
                localization.number_format,
            ),
            "supplier_paid_total": format_currency(
                float(payment_summary["approved_total"]),
                localization.currency,
                localization.number_format,
            ),
            "supplier_outstanding": format_currency(
                float(payment_summary["outstanding_payable"]),
                localization.currency,
                localization.number_format,
            ),
        }

        top_products_view = [
            {
                "product_name": row.product_name,
                "product_sku": row.product_sku,
                "total_quantity_sold": row.total_quantity_sold,
                "total_revenue": row.total_revenue,
                "total_revenue_formatted": format_currency(
                    float(row.total_revenue or 0.0),
                    localization.currency,
                    localization.number_format,
                ),
            }
            for row in top_products
        ]
        category_sales_view = [
            {
                "category_name": row.category_name,
                "total_quantity_sold": row.total_quantity_sold,
                "total_revenue": row.total_revenue,
                "total_revenue_formatted": format_currency(
                    float(row.total_revenue or 0.0),
                    localization.currency,
                    localization.number_format,
                ),
            }
            for row in category_sales
        ]
        top_customers_view = [
            {
                "customer_name": row.customer_name,
                "customer_email": row.customer_email,
                "order_count": row.order_count,
                "total_spent": row.total_spent,
                "total_spent_formatted": format_currency(
                    float(row.total_spent or 0.0),
                    localization.currency,
                    localization.number_format,
                ),
                "points_balance": row.points_balance,
            }
            for row in top_customers
        ]

        return {
            "period_label": {
                "today": "Today",
                "7d": "Last 7 Days",
                "30d": "Last 30 Days",
                "month": "This Month",
                "all": "All Time",
            }[period],
            "localized": localized,
            "sales_summary": sales_summary,
            "top_products": top_products_view,
            "category_sales": category_sales_view,
            "low_stock_products": low_stock_products,
            "top_customers": top_customers_view,
            "executive_summary": executive_summary,
        }

    @expose("/reports", methods=["GET"])
    async def reports_page(self, request: Request):
        db = SessionLocal()
        try:
            localization = get_localization_setting(db, _selected_tenant_id(request))
            period = request.query_params.get("period", "30d")

            shift_reports = (
                db.query(ShiftReconciliation)
                .options(
                    joinedload(ShiftReconciliation.drawer_session),
                    joinedload(ShiftReconciliation.closed_by_user),
                )
                .order_by(ShiftReconciliation.id.desc())
                .limit(10)
                .all()
            )

            cache_key = (period, localization.currency, localization.number_format)
            cached = _reports_cache.get(cache_key)
            now = datetime.now(UTC).timestamp()
            if cached and now - cached[0] < REPORTS_CACHE_SECONDS:
                data = cached[1]
            else:
                data = self._build_report_data(db, period, localization)
                _reports_cache[cache_key] = (
                    now,
                    {
                        k: (v.copy() if isinstance(v, dict) else v)
                        for k, v in data.items()
                    },
                )

            return await self.templates.TemplateResponse(
                request,
                "reports.html",
                context={
                    "request": request,
                    "title": "Reports Dashboard",
                    "period": period,
                    "period_label": data["period_label"],
                    "localization": localization,
                    "localized": data["localized"],
                    "sales_summary": data["sales_summary"],
                    "top_products": data["top_products"],
                    "category_sales": data["category_sales"],
                    "low_stock_products": data["low_stock_products"],
                    "top_customers": data["top_customers"],
                    "executive_summary": data["executive_summary"],
                    "shift_reports": shift_reports,
                },
            )
        finally:
            db.close()

    @expose("/reports/shift/{reconciliation_id}/print", methods=["GET"])
    async def shift_report_print_page(self, request: Request, reconciliation_id: int):
        """Print-friendly Z-report for a closed drawer shift (admin session)."""
        from datetime import datetime as _dt

        from app.services.reports import get_shift_report_data

        db = SessionLocal()
        try:
            data = get_shift_report_data(db=db, reconciliation_id=reconciliation_id)
            if data is None:
                raise HTTPException(status_code=404)
            rec = data["reconciliation"]
            drawer = data["drawer"]
            report = {
                "reconciliation_id": rec.id,
                "drawer_session_id": rec.drawer_session_id,
                "opened_at": drawer.opened_at if drawer else None,
                "closed_at": drawer.closed_at if drawer else None,
                "operator_name": data["operator_name"],
                "closed_by_name": data["closed_by_name"],
                "starting_cash": float(drawer.starting_cash or 0.0) if drawer else 0.0,
                "expected_cash": float(rec.expected_cash or 0.0),
                "counted_cash": float(rec.counted_cash or 0.0),
                "cash_variance": float(rec.cash_variance or 0.0),
                "expected_non_cash": float(rec.expected_non_cash or 0.0),
                "counted_non_cash": float(rec.counted_non_cash or 0.0),
                "non_cash_variance": float(rec.non_cash_variance or 0.0),
                "cash_sales_total": float(rec.cash_sales_total or 0.0),
                "non_cash_sales_total": float(rec.non_cash_sales_total or 0.0),
                "refunds_total": float(rec.refunds_total or 0.0),
                "gross_sales_total": float(rec.gross_sales_total or 0.0),
                "net_sales_total": float(rec.net_sales_total or 0.0),
                "completed_order_count": int(rec.completed_order_count or 0),
                "payment_breakdown": data["payment_breakdown"],
            }
            return await self.templates.TemplateResponse(
                request,
                "report_shift.html",
                context={
                    "report": report,
                    "now": _dt.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
                    "title": f"Shift Report #{rec.id}",
                },
            )
        finally:
            db.close()


class WorkflowsAdmin(BaseView):
    """Guided admin workflows: restock, invoicing, drawer close, refunds.

    Each wizard is a stateless step chain under one route, driving the same
    service layer the public API uses (``app.services.*``).
    """

    name = "Workflows"
    icon = "fa-solid fa-wand-magic-sparkles"
    category = "Workflows"
    category_icon = "fa-solid fa-bolt"

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _admin_user(db, request):
        return db.get(User, request.session.get("admin_user_id"))

    @staticmethod
    def _flash_http_error(request, exc: HTTPException):
        Flash.error(request, str(exc.detail), "Action failed")

    @staticmethod
    def _previously_billed_map(db, po_item_ids) -> dict[int, int]:
        if not po_item_ids:
            return {}
        rows = (
            db.query(
                PurchaseInvoiceItem.purchase_order_item_id,
                func.coalesce(func.sum(PurchaseInvoiceItem.billed_quantity), 0),
            )
            .join(
                PurchaseInvoice,
                PurchaseInvoiceItem.invoice_id == PurchaseInvoice.id,
            )
            .filter(
                PurchaseInvoiceItem.purchase_order_item_id.in_(po_item_ids),
                PurchaseInvoice.status != "rejected",
            )
            .group_by(PurchaseInvoiceItem.purchase_order_item_id)
            .all()
        )
        return {row[0]: int(row[1] or 0) for row in rows}

    @staticmethod
    def _already_refunded_map(db, order_item_ids) -> dict[int, int]:
        if not order_item_ids:
            return {}
        rows = (
            db.query(
                RefundItem.order_item_id,
                func.coalesce(func.sum(RefundItem.quantity), 0),
            )
            .filter(RefundItem.order_item_id.in_(order_item_ids))
            .group_by(RefundItem.order_item_id)
            .all()
        )
        return {row[0]: int(row[1] or 0) for row in rows}

    # --------------------------------------------------------------- hub page

    @expose("/workflows", methods=["GET"])
    async def workflows_index(self, request: Request):
        db = SessionLocal()
        try:
            low_stock_count = (
                db.query(Product)
                .filter(
                    Product.stock_quantity <= Product.reorder_point,
                    Product.tenant_id == _selected_tenant_id(request),
                )
                .count()
            )
            draft_po_count = (
                db.query(PurchaseOrder)
                .filter(
                    PurchaseOrder.status == "draft",
                    PurchaseOrder.tenant_id == _selected_tenant_id(request),
                )
                .count()
            )
            pending_invoice_count = (
                db.query(PurchaseInvoice)
                .filter(
                    PurchaseInvoice.status == "pending_review",
                    PurchaseInvoice.tenant_id == _selected_tenant_id(request),
                )
                .count()
            )
            pending_payment_count = (
                db.query(SupplierPayment)
                .filter(
                    SupplierPayment.status == "pending_review",
                    SupplierPayment.tenant_id == _selected_tenant_id(request),
                )
                .count()
            )
            open_drawer_count = (
                db.query(DrawerSession)
                .filter(
                    DrawerSession.status == "open",
                    DrawerSession.tenant_id == _selected_tenant_id(request),
                )
                .count()
            )
            return await self.templates.TemplateResponse(
                request,
                "workflows/index.html",
                context={
                    "title": "Workflows",
                    "low_stock_count": low_stock_count,
                    "draft_po_count": draft_po_count,
                    "pending_invoice_count": pending_invoice_count,
                    "pending_payment_count": pending_payment_count,
                    "open_drawer_count": open_drawer_count,
                },
            )
        finally:
            db.close()

    # ----------------------------------------------------------- restock flow

    @expose("/workflows/restock", methods=["GET", "POST"])
    async def restock_workflow(self, request: Request):
        db = SessionLocal()
        try:
            step = request.query_params.get("step", "generate")
            pending_product_ids = {
                row[0]
                for row in db.query(PurchaseOrderItem.product_id)
                .join(
                    PurchaseOrder,
                    PurchaseOrderItem.purchase_order_id == PurchaseOrder.id,
                )
                .filter(
                    PurchaseOrder.status.in_(
                        ("draft", "ordered", "partially_received")
                    ),
                    PurchaseOrder.tenant_id == _selected_tenant_id(request),
                )
                .all()
            }
            low_stock_query = db.query(Product).filter(
                Product.stock_quantity <= Product.reorder_point,
                Product.tenant_id == _selected_tenant_id(request),
            )
            if pending_product_ids:
                low_stock_query = low_stock_query.filter(
                    Product.id.notin_(pending_product_ids)
                )
            low_stock = low_stock_query.order_by(Product.id.asc()).all()

            if request.method == "POST":
                form = await request.form()
                step = form.get("step") or step
                if step == "generate":
                    try:
                        lookback_days = int(form.get("lookback_days") or 30)
                    except (TypeError, ValueError):
                        lookback_days = 30
                    result = auto_generate_purchase_orders(
                        db=db, lookback_days=lookback_days
                    )
                    if result["generated"]:
                        Flash.success(
                            request,
                            f"Generated {result['generated']} purchase order(s) "
                            f"for {', '.join(result['suppliers'])}.",
                        )
                    elif result["skipped_products"]:
                        reasons = {
                            item["reason"] for item in result["skipped_products"]
                        }
                        Flash.warning(
                            request,
                            "No POs generated. " + "; ".join(sorted(reasons)),
                        )
                    else:
                        Flash.info(request, "Nothing to reorder right now.")
                    return RedirectResponse(
                        url="/admin/workflows/restock?step=receive", status_code=303
                    )

                if step == "select_po":
                    try:
                        po_id = int(form.get("po_id") or "")
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Select a PO"
                        ) from None
                    return RedirectResponse(
                        url=f"/admin/workflows/restock?step=receive&po_id={po_id}",
                        status_code=303,
                    )

                if step == "create":
                    try:
                        supplier_id = int(form.get("supplier_id") or "")
                    except (TypeError, ValueError):
                        supplier_id = 0
                    try:
                        if supplier_id <= 0:
                            raise HTTPException(
                                status_code=400, detail="Select a supplier"
                            )
                        items = []
                        for key, value in form.multi_items():
                            if not key.startswith("qty_"):
                                continue
                            try:
                                product_id = int(key.removeprefix("qty_"))
                                qty = int(value)
                            except (TypeError, ValueError):
                                continue
                            if qty <= 0:
                                continue
                            try:
                                unit_cost = float(form.get(f"cost_{product_id}") or 0)
                            except (TypeError, ValueError):
                                unit_cost = 0.0
                            items.append(
                                PurchaseOrderItemCreate(
                                    product_id=product_id,
                                    quantity_ordered=qty,
                                    unit_cost=unit_cost,
                                )
                            )
                        if not items:
                            raise HTTPException(
                                status_code=400,
                                detail="Enter at least one product with a quantity",
                            )
                        user = self._admin_user(db, request)
                        if user is None:
                            raise HTTPException(
                                status_code=403, detail="Admin user missing"
                            )
                        purchase_order = create_purchase_order(
                            db=db,
                            current_user=user,
                            purchase_order_in=PurchaseOrderCreate(
                                supplier_id=supplier_id,
                                items=items,
                                notes=form.get("notes") or None,
                            ),
                            tenant_id=_selected_tenant_id(request),
                        )
                    except HTTPException as exc:
                        self._flash_http_error(request, exc)
                        return RedirectResponse(
                            url="/admin/workflows/restock?step=create",
                            status_code=303,
                        )
                    Flash.success(
                        request, f"Purchase order #{purchase_order.id} created (draft)."
                    )
                    return RedirectResponse(
                        url=f"/admin/workflows/restock?step=receive&po_id={purchase_order.id}",
                        status_code=303,
                    )

                if step == "order":
                    try:
                        po_id = int(form.get("po_id") or "")
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Select a PO"
                        ) from None
                    try:
                        user = self._admin_user(db, request)
                        if user is None:
                            raise HTTPException(
                                status_code=403, detail="Admin user missing"
                            )
                        tenant_id = _selected_tenant_id(request)
                        submit_purchase_order_for_review(
                            db=db,
                            current_user=user,
                            purchase_order_id=po_id,
                            action_in=PurchaseOrderReviewAction(review_note=None),
                            tenant_id=tenant_id,
                        )
                        mark_purchase_order_ordered(
                            db=db,
                            current_user=user,
                            purchase_order_id=po_id,
                            action_in=PurchaseOrderReviewAction(review_note=None),
                            tenant_id=tenant_id,
                        )
                    except HTTPException as exc:
                        self._flash_http_error(request, exc)
                        return RedirectResponse(
                            url=f"/admin/workflows/restock?step=receive&po_id={po_id}",
                            status_code=303,
                        )
                    Flash.success(
                        request, f"PO #{po_id} reviewed and marked as ordered."
                    )
                    return RedirectResponse(
                        url=f"/admin/workflows/restock?step=receive&po_id={po_id}",
                        status_code=303,
                    )

                if step == "receive":
                    try:
                        po_id = int(form.get("po_id") or "")
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Select a PO"
                        ) from None
                    items = []
                    for key, value in form.multi_items():
                        if not key.startswith("qty_"):
                            continue
                        try:
                            item_id = int(key.removeprefix("qty_"))
                            qty = int(value)
                        except (TypeError, ValueError):
                            continue
                        if qty > 0:
                            items.append(
                                PurchaseOrderReceiveItem(
                                    purchase_order_item_id=item_id,
                                    quantity_received=qty,
                                )
                            )
                    if not items:
                        raise HTTPException(
                            status_code=400,
                            detail="Enter at least one received quantity",
                        )
                    try:
                        user = self._admin_user(db, request)
                        if user is None:
                            raise HTTPException(
                                status_code=403, detail="Admin user missing"
                            )
                        receive_purchase_order_items(
                            db=db,
                            current_user=user,
                            purchase_order_id=po_id,
                            receive_in=PurchaseOrderReceive(items=items),
                            tenant_id=_selected_tenant_id(request),
                        )
                    except HTTPException as exc:
                        self._flash_http_error(request, exc)
                        return RedirectResponse(
                            url="/admin/workflows/restock?step=receive", status_code=303
                        )
                    Flash.success(request, f"PO #{po_id} received — stock updated.")
                    return RedirectResponse(
                        url=f"/admin/workflows/restock?step=done&po_id={po_id}",
                        status_code=303,
                    )

            draft_pos = (
                db.query(PurchaseOrder)
                .options(
                    joinedload(PurchaseOrder.items).joinedload(
                        PurchaseOrderItem.product
                    ),
                    joinedload(PurchaseOrder.supplier),
                )
                .filter(
                    PurchaseOrder.status.in_(["draft", "ordered"]),
                    PurchaseOrder.tenant_id == _selected_tenant_id(request),
                )
                .order_by(PurchaseOrder.id.asc())
                .all()
            )
            suppliers = (
                db.query(Supplier)
                .filter(
                    Supplier.is_active.is_(True),
                    Supplier.tenant_id == _selected_tenant_id(request),
                )
                .order_by(Supplier.name.asc())
                .all()
            )
            catalog_products = (
                db.query(Product)
                .filter(Product.tenant_id == _selected_tenant_id(request))
                .order_by(Product.name.asc())
                .all()
            )
            selected_po = None
            po_id = request.query_params.get("po_id")
            if po_id:
                selected_po = next(
                    (po for po in draft_pos if po.id == int(po_id)),
                    None,
                )
            return await self.templates.TemplateResponse(
                request,
                "workflows/restock.html",
                context={
                    "title": "Restock",
                    "step": step,
                    "low_stock": low_stock,
                    "draft_pos": draft_pos,
                    "suppliers": suppliers,
                    "catalog_products": catalog_products,
                    "selected_po": selected_po,
                    "done_po_id": request.query_params.get("po_id"),
                },
            )
        except HTTPException as exc:
            self._flash_http_error(request, exc)
            return RedirectResponse(
                url="/admin/workflows/restock?step=generate", status_code=303
            )
        finally:
            db.close()

    # --------------------------------------------------------- review queue

    @expose("/workflows/review", methods=["GET", "POST"])
    async def review_workflow(self, request: Request):
        """Resolve purchase invoices and supplier payments stuck in review.

        Superuser-only by design (the panel admits only superusers): the acting
        admin user bypasses the service-layer self-approval guard, so documents
        nobody can otherwise approve get a resolution path.
        """
        db = SessionLocal()
        try:
            if request.method == "POST":
                form = await request.form()
                kind = form.get("kind")
                doc_id = form.get("id")
                action = form.get("action")
                try:
                    doc_id = int(doc_id or "")
                except (TypeError, ValueError):
                    raise HTTPException(
                        status_code=400, detail="Invalid document id"
                    ) from None
                user = self._admin_user(db, request)
                if user is None:
                    raise HTTPException(status_code=403, detail="Admin user missing")
                review_note = form.get("review_note") or None
                tenant_id = _selected_tenant_id(request)
                if kind == "invoice" and action in ("approve", "reject"):
                    action_in = PurchaseInvoiceReviewAction(review_note=review_note)
                    if action == "approve":
                        approve_purchase_invoice(
                            db=db,
                            current_user=user,
                            invoice_id=doc_id,
                            action_in=action_in,
                            tenant_id=tenant_id,
                        )
                    else:
                        reject_purchase_invoice(
                            db=db,
                            current_user=user,
                            invoice_id=doc_id,
                            action_in=action_in,
                            tenant_id=tenant_id,
                        )
                    Flash.success(request, f"Invoice #{doc_id} {action}ed.")
                elif kind == "payment" and action in ("approve", "reject"):
                    action_in = SupplierPaymentReviewAction(review_note=review_note)
                    if action == "approve":
                        approve_supplier_payment(
                            db=db,
                            current_user=user,
                            payment_id=doc_id,
                            action_in=action_in,
                            tenant_id=tenant_id,
                        )
                    else:
                        reject_supplier_payment(
                            db=db,
                            current_user=user,
                            payment_id=doc_id,
                            action_in=action_in,
                            tenant_id=tenant_id,
                        )
                    Flash.success(request, f"Payment #{doc_id} {action}ed.")
                else:
                    raise HTTPException(status_code=400, detail="Unknown review action")
                return RedirectResponse(url="/admin/workflows/review", status_code=303)

            tenant_id = _selected_tenant_id(request)
            pending_invoices = (
                db.query(PurchaseInvoice)
                .options(
                    joinedload(PurchaseInvoice.supplier),
                    joinedload(PurchaseInvoice.user),
                )
                .filter(
                    PurchaseInvoice.status == "pending_review",
                    PurchaseInvoice.tenant_id == tenant_id,
                )
                .order_by(PurchaseInvoice.id.asc())
                .all()
            )
            pending_payments = (
                db.query(SupplierPayment)
                .options(
                    joinedload(SupplierPayment.supplier),
                    joinedload(SupplierPayment.invoice),
                    joinedload(SupplierPayment.user),
                )
                .filter(
                    SupplierPayment.status == "pending_review",
                    SupplierPayment.tenant_id == tenant_id,
                )
                .order_by(SupplierPayment.id.asc())
                .all()
            )
            return await self.templates.TemplateResponse(
                request,
                "workflows/review.html",
                context={
                    "title": "Review Queue",
                    "pending_invoices": pending_invoices,
                    "pending_payments": pending_payments,
                },
            )
        except HTTPException as exc:
            self._flash_http_error(request, exc)
            return RedirectResponse(url="/admin/workflows/review", status_code=303)
        finally:
            db.close()

    # ----------------------------------------------------------- invoice flow

    @expose("/workflows/invoice", methods=["GET", "POST"])
    async def invoice_workflow(self, request: Request):
        db = SessionLocal()
        try:
            step = request.query_params.get("step", "select")
            eligible_pos = []
            pos = (
                db.query(PurchaseOrder)
                .options(
                    joinedload(PurchaseOrder.items).joinedload(
                        PurchaseOrderItem.product
                    ),
                    joinedload(PurchaseOrder.supplier),
                )
                .filter(
                    PurchaseOrder.status != "cancelled",
                    PurchaseOrder.tenant_id == _selected_tenant_id(request),
                )
                .order_by(PurchaseOrder.id.desc())
                .limit(50)
                .all()
            )
            po_item_ids = [
                item.id for po in pos for item in po.items if item.quantity_received > 0
            ]
            billed_map = self._previously_billed_map(db, po_item_ids)
            for po in pos:
                remaining = sum(
                    max(item.quantity_received - billed_map.get(item.id, 0), 0)
                    for item in po.items
                    if item.quantity_received > 0
                )
                if remaining > 0:
                    eligible_pos.append((po, remaining))

            if request.method == "POST":
                form = await request.form()
                step = form.get("step") or step
                if step == "select":
                    try:
                        po_id = int(form.get("po_id") or "")
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Select a PO"
                        ) from None
                    return RedirectResponse(
                        url=f"/admin/workflows/invoice?step=create&po_id={po_id}",
                        status_code=303,
                    )

                if step == "create":
                    po_id = int(request.query_params.get("po_id"))
                    invoice_number = (form.get("invoice_number") or "").strip()
                    if not invoice_number:
                        raise HTTPException(
                            status_code=400, detail="Invoice number is required"
                        )
                    items = []
                    for key, value in form.multi_items():
                        if key.startswith("bill_qty_"):
                            item_id = int(key.removeprefix("bill_qty_"))
                            qty = int(value or 0)
                            if qty > 0:
                                try:
                                    cost = float(form.get(f"bill_cost_{item_id}") or 0)
                                except (TypeError, ValueError):
                                    cost = 0.0
                                items.append(
                                    PurchaseInvoiceItemCreate(
                                        purchase_order_item_id=item_id,
                                        billed_quantity=qty,
                                        billed_unit_cost=cost,
                                    )
                                )
                    if not items:
                        raise HTTPException(
                            status_code=400,
                            detail="Enter at least one billed line",
                        )
                    try:
                        user = self._admin_user(db, request)
                        if user is None:
                            raise HTTPException(
                                status_code=403, detail="Admin user missing"
                            )
                        invoice = create_purchase_invoice(
                            db=db,
                            current_user=user,
                            invoice_in=PurchaseInvoiceCreate(
                                purchase_order_id=po_id,
                                invoice_number=invoice_number,
                                items=items,
                            ),
                            tenant_id=_selected_tenant_id(request),
                        )
                    except HTTPException as exc:
                        self._flash_http_error(request, exc)
                        return RedirectResponse(
                            url=f"/admin/workflows/invoice?step=create&po_id={po_id}",
                            status_code=303,
                        )
                    Flash.success(
                        request,
                        f"Invoice {invoice.invoice_number} created.",
                    )
                    return RedirectResponse(
                        url=(
                            f"/admin/workflows/invoice?step=review"
                            f"&invoice_id={invoice.id}"
                        ),
                        status_code=303,
                    )

                if step == "review":
                    invoice_id = int(request.query_params.get("invoice_id"))
                    action_name = form.get("action")
                    review_note = form.get("review_note") or None
                    try:
                        user = self._admin_user(db, request)
                        if user is None:
                            raise HTTPException(
                                status_code=403, detail="Admin user missing"
                            )
                        if action_name == "submit":
                            submit_purchase_invoice_for_review(
                                db=db,
                                current_user=user,
                                invoice_id=invoice_id,
                                action_in=PurchaseInvoiceReviewAction(
                                    review_note=review_note
                                ),
                                tenant_id=_selected_tenant_id(request),
                            )
                            Flash.success(
                                request, f"Invoice #{invoice_id} submitted for review."
                            )
                        elif action_name == "approve":
                            approve_purchase_invoice(
                                db=db,
                                current_user=user,
                                invoice_id=invoice_id,
                                action_in=PurchaseInvoiceReviewAction(
                                    review_note=review_note
                                ),
                                tenant_id=_selected_tenant_id(request),
                            )
                            Flash.success(request, f"Invoice #{invoice_id} approved.")
                        elif action_name == "reject":
                            reject_purchase_invoice(
                                db=db,
                                current_user=user,
                                invoice_id=invoice_id,
                                action_in=PurchaseInvoiceReviewAction(
                                    review_note=review_note
                                ),
                                tenant_id=_selected_tenant_id(request),
                            )
                            Flash.success(request, f"Invoice #{invoice_id} rejected.")
                        else:
                            raise HTTPException(
                                status_code=400, detail="Unknown review action"
                            )
                    except HTTPException as exc:
                        self._flash_http_error(request, exc)
                        return RedirectResponse(
                            url=(
                                f"/admin/workflows/invoice?step=review"
                                f"&invoice_id={invoice_id}"
                            ),
                            status_code=303,
                        )
                    return RedirectResponse(
                        url=f"/admin/purchase-invoice/details/{invoice_id}",
                        status_code=303,
                    )

            po_id = request.query_params.get("po_id")
            po = None
            invoice_items = []
            if po_id and step == "create":
                po = next((p for p, _ in eligible_pos if p.id == int(po_id)), None)
                if po is None:
                    po = (
                        db.query(PurchaseOrder)
                        .options(
                            joinedload(PurchaseOrder.items).joinedload(
                                PurchaseOrderItem.product
                            ),
                            joinedload(PurchaseOrder.supplier),
                        )
                        .filter(PurchaseOrder.id == int(po_id))
                        .first()
                    )
                if po is not None:
                    item_ids = [item.id for item in po.items]
                    billed_map = self._previously_billed_map(db, item_ids)
                    invoice_items = [
                        {
                            "po_item": item,
                            "remaining": max(
                                item.quantity_received - billed_map.get(item.id, 0),
                                0,
                            ),
                        }
                        for item in po.items
                        if item.quantity_received > 0
                    ]

            invoice = None
            invoice_id = request.query_params.get("invoice_id")
            if invoice_id and step == "review":
                invoice = (
                    db.query(PurchaseInvoice)
                    .options(
                        joinedload(PurchaseInvoice.items).joinedload(
                            PurchaseInvoiceItem.product
                        ),
                        joinedload(PurchaseInvoice.supplier),
                    )
                    .filter(PurchaseInvoice.id == int(invoice_id))
                    .first()
                )

            return await self.templates.TemplateResponse(
                request,
                "workflows/invoice.html",
                context={
                    "title": "Invoicing",
                    "step": step,
                    "eligible_pos": eligible_pos,
                    "po": po,
                    "invoice_items": invoice_items,
                    "invoice": invoice,
                },
            )
        except HTTPException as exc:
            self._flash_http_error(request, exc)
            return RedirectResponse(
                url="/admin/workflows/invoice?step=select", status_code=303
            )
        finally:
            db.close()

    # ------------------------------------------------------- drawer close flow

    @expose("/workflows/close-drawer", methods=["GET", "POST"])
    async def close_drawer_workflow(self, request: Request):
        db = SessionLocal()
        try:
            step = request.query_params.get("step", "select")
            open_drawers = (
                db.query(DrawerSession)
                .options(joinedload(DrawerSession.user))
                .filter(DrawerSession.status == "open")
                .order_by(DrawerSession.id.asc())
                .all()
            )

            if request.method == "POST":
                form = await request.form()
                step = form.get("step") or step
                if step == "select":
                    try:
                        drawer_id = int(form.get("drawer_id") or "")
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Select a drawer session"
                        ) from None
                    return RedirectResponse(
                        url=(
                            f"/admin/workflows/close-drawer?step=count"
                            f"&drawer_id={drawer_id}"
                        ),
                        status_code=303,
                    )

                if step == "count":
                    drawer_id = int(request.query_params.get("drawer_id"))
                    drawer = db.get(DrawerSession, drawer_id)
                    if not drawer or drawer.status != "open":
                        raise HTTPException(
                            status_code=400,
                            detail="Only open drawer sessions can be reconciled.",
                        )
                    existing = (
                        db.query(ShiftReconciliation)
                        .filter(ShiftReconciliation.drawer_session_id == drawer_id)
                        .first()
                    )
                    if existing:
                        raise HTTPException(
                            status_code=400,
                            detail="This drawer session has already been reconciled.",
                        )
                    try:
                        counted_cash = float(form.get("counted_cash") or 0)
                        counted_non_cash = form.get("counted_non_cash")
                        counted_non_cash = (
                            float(counted_non_cash) if counted_non_cash else None
                        )
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Counted cash must be a number"
                        ) from None
                    user = self._admin_user(db, request)
                    if user is None:
                        raise HTTPException(
                            status_code=403, detail="Admin user missing"
                        )
                    reconciliation = build_reconciliation(
                        db=db,
                        drawer=drawer,
                        closed_by_user_id=user.id,
                        reconcile_in=ShiftReconciliationCreate(
                            counted_cash=counted_cash,
                            counted_non_cash=counted_non_cash,
                            notes=form.get("notes") or None,
                        ),
                    )
                    db.add(reconciliation)
                    drawer.ending_cash = counted_cash
                    drawer.expected_cash = reconciliation.expected_cash
                    drawer.closed_at = datetime.now(UTC)
                    drawer.status = "closed"
                    db.add(drawer)
                    log_action(
                        db=db,
                        action="drawer.reconcile",
                        user_id=user.id,
                        resource_type="drawer_session",
                        resource_id=drawer.id,
                        details={
                            "expected_cash": str(reconciliation.expected_cash),
                            "counted_cash": str(counted_cash),
                        },
                    )
                    db.commit()
                    db.refresh(reconciliation)
                    Flash.success(request, f"Drawer #{drawer.id} closed.")
                    return RedirectResponse(
                        url=(
                            f"/admin/workflows/close-drawer?step=done"
                            f"&recon_id={reconciliation.id}"
                        ),
                        status_code=303,
                    )

            drawer = None
            totals = None
            expected_cash = None
            expected_non_cash = None
            drawer_id = request.query_params.get("drawer_id")
            if drawer_id and step == "count":
                drawer = db.get(DrawerSession, int(drawer_id))
                if drawer and drawer.status == "open":
                    totals = compute_drawer_totals(db, drawer)
                    expected_cash = float(drawer.starting_cash or 0.0)
                    expected_cash += totals["cash_sales_total"]
                    expected_cash -= totals["cash_refunds_total"]
                    expected_non_cash = totals["non_cash_sales_total"]
                    expected_non_cash -= totals["non_cash_refunds_total"]

            return await self.templates.TemplateResponse(
                request,
                "workflows/close_drawer.html",
                context={
                    "title": "Close Drawer",
                    "step": step,
                    "open_drawers": open_drawers,
                    "drawer": drawer,
                    "totals": totals,
                    "expected_cash": expected_cash,
                    "expected_non_cash": expected_non_cash,
                    "done_recon_id": request.query_params.get("recon_id"),
                },
            )
        except HTTPException as exc:
            self._flash_http_error(request, exc)
            return RedirectResponse(
                url="/admin/workflows/close-drawer?step=select", status_code=303
            )
        finally:
            db.close()

    # ------------------------------------------------------------ refund flow

    @expose("/workflows/refund", methods=["GET", "POST"])
    async def refund_workflow(self, request: Request):
        db = SessionLocal()
        try:
            step = request.query_params.get("step", "select")
            completed_orders = (
                db.query(Order)
                .options(joinedload(Order.items))
                .filter(Order.status.in_(["serving", "completed"]))
                .order_by(Order.id.desc())
                .limit(50)
                .all()
            )
            order_item_ids = [
                item.id for order in completed_orders for item in order.items
            ]
            refunded_map = self._already_refunded_map(db, order_item_ids)
            completed_order_rows = [
                {
                    "order": order,
                    "refundable_count": sum(
                        max(
                            item.quantity - refunded_map.get(item.id, 0),
                            0,
                        )
                        for item in order.items
                    ),
                }
                for order in completed_orders
            ]

            if request.method == "POST":
                form = await request.form()
                step = form.get("step") or step
                if step == "select":
                    try:
                        order_id = int(form.get("order_id") or "")
                    except (TypeError, ValueError):
                        raise HTTPException(
                            status_code=400, detail="Select an order"
                        ) from None
                    return RedirectResponse(
                        url=f"/admin/workflows/refund?step=items&order_id={order_id}",
                        status_code=303,
                    )

                if step == "items":
                    order_id = int(request.query_params.get("order_id"))
                    items = []
                    for key, value in form.multi_items():
                        if not key.startswith("refund_qty_"):
                            continue
                        try:
                            item_id = int(key.removeprefix("refund_qty_"))
                            qty = int(value)
                        except (TypeError, ValueError):
                            continue
                        if qty > 0:
                            items.append(
                                RefundItemCreate(
                                    order_item_id=item_id,
                                    quantity=qty,
                                )
                            )
                    if not items:
                        raise HTTPException(
                            status_code=400,
                            detail="Enter at least one refund quantity",
                        )
                    try:
                        user = self._admin_user(db, request)
                        if user is None:
                            raise HTTPException(
                                status_code=403, detail="Admin user missing"
                            )
                        refund = create_refund(
                            db=db,
                            current_user=user,
                            refund_in=RefundCreate(
                                order_id=order_id,
                                reason=form.get("reason") or None,
                                payment_method=(form.get("payment_method") or None),
                                idempotency_key=str(uuid4()),
                                items=items,
                            ),
                            tenant_id=_selected_tenant_id(request),
                        )
                    except HTTPException as exc:
                        self._flash_http_error(request, exc)
                        return RedirectResponse(
                            url=(
                                f"/admin/workflows/refund?step=items"
                                f"&order_id={order_id}"
                            ),
                            status_code=303,
                        )
                    Flash.success(request, f"Refund #{refund.id} recorded.")
                    return RedirectResponse(
                        url=f"/admin/workflows/refund?step=done&refund_id={refund.id}",
                        status_code=303,
                    )

            order = None
            refund_items = []
            order_id = request.query_params.get("order_id")
            if order_id and step == "items":
                order = next(
                    (o for o in completed_orders if o.id == int(order_id)),
                    None,
                )
                if order is not None:
                    item_ids = [item.id for item in order.items]
                    refunded_map = self._already_refunded_map(db, item_ids)
                    refund_items = [
                        {
                            "order_item": item,
                            "refundable": max(
                                item.quantity - refunded_map.get(item.id, 0),
                                0,
                            ),
                        }
                        for item in order.items
                    ]

            return await self.templates.TemplateResponse(
                request,
                "workflows/refund.html",
                context={
                    "title": "Refund",
                    "step": step,
                    "completed_orders": completed_order_rows,
                    "order": order,
                    "refund_items": refund_items,
                    "done_refund_id": request.query_params.get("refund_id"),
                },
            )
        except HTTPException as exc:
            self._flash_http_error(request, exc)
            return RedirectResponse(
                url="/admin/workflows/refund?step=select", status_code=303
            )
        finally:
            db.close()
