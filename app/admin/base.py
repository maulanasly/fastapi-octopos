import re
from typing import Any

# pyrefly: ignore [missing-import]
from sqladmin import ModelView
from sqladmin.filters import ForeignKeyFilter

# pyrefly: ignore [missing-import]
from starlette.requests import Request

from app.admin.formatting import _make_relation_formatter
from app.models.tenant import Tenant

REPORTS_CACHE_SECONDS = 120
_reports_cache: dict[tuple[int, str, str, str], tuple[float, dict]] = {}

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
