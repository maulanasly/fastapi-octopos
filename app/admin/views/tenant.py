from typing import Any

# pyrefly: ignore [missing-import]
from sqladmin import BaseView, ModelView, expose
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.admin.base import _selected_tenant_id, _unique_tenant_slug
from app.core.database import SessionLocal
from app.models.tenant import Tenant


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

    name = "Active Tenant"
    icon = "fa-solid fa-building-circle-arrow-right"
    category = "Platform"

    @expose("/tenant", methods=["GET", "POST"])
    async def tenant_switch(self, request: Request):
        if request.method == "POST":
            form = await request.form()
            raw = form.get("tenant_id")
            nxt = (form.get("next") or "").strip()
            if str(raw).isdigit():
                request.session["admin_tenant_id"] = int(raw)
                # Allow dashboard inline switcher to return to originating page
                if nxt.startswith("/admin"):
                    return RedirectResponse(url=nxt, status_code=303)
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
