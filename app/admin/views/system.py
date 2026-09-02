from typing import Any

from sqladmin.filters import BooleanFilter

# pyrefly: ignore [missing-import]
from starlette.requests import Request
from wtforms import SelectField

from app.admin.base import TenantScopedModelView, _selected_tenant_id
from app.admin.formatting import LabeledRelationsMixin
from app.core.database import SessionLocal
from app.core.localization import (
    SUPPORTED_COUNTRY_CODES,
    SUPPORTED_CURRENCIES,
    SUPPORTED_DATE_FORMATS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_NUMBER_FORMATS,
    SUPPORTED_TIMEZONES,
)
from app.models.localization import LocalizationSetting
from app.models.purchasing_setting import PurchasingSetting
from app.models.sync_event import SyncEventLog


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
    column_labels = {
        LocalizationSetting.tenant: "Tenant",
        LocalizationSetting.language: "Language",
        LocalizationSetting.timezone: "Timezone",
        LocalizationSetting.currency: "Currency",
        LocalizationSetting.date_format: "Date Format",
        LocalizationSetting.number_format: "Number Format",
        LocalizationSetting.country_code: "Country",
        LocalizationSetting.updated_at: "Updated",
    }
    column_descriptions = {
        LocalizationSetting.language: "UI language for the selected tenant",
        LocalizationSetting.timezone: "IANA timezone for receipts and reports",
        LocalizationSetting.currency: "Display currency (amounts stored as cents)",
    }
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


class PurchasingSettingAdmin(
    LabeledRelationsMixin, TenantScopedModelView, model=PurchasingSetting
):
    name = "Purchasing Automation"
    icon = "fa-solid fa-robot"
    category = "Purchasing"
    category_icon = "fa-solid fa-truck"

    exclude_tenant_from_form = False

    column_list = [
        PurchasingSetting.id,
        PurchasingSetting.tenant,
        PurchasingSetting.auto_po_enabled,
        PurchasingSetting.auto_po_lookback_days,
        PurchasingSetting.auto_po_min_stock_trigger,
    ]
    column_labels = {
        PurchasingSetting.tenant: "Tenant",
        PurchasingSetting.auto_po_enabled: "Auto PO",
        PurchasingSetting.auto_po_lookback_days: "Lookback (days)",
        PurchasingSetting.auto_po_min_stock_trigger: "Min Stock Trigger",
    }
    column_descriptions = {
        PurchasingSetting.auto_po_enabled: "When enabled, auto_generate_purchase_orders creates drafts nightly",
        PurchasingSetting.auto_po_lookback_days: "Sales velocity window for reorder suggestions",
    }
    column_filters = [BooleanFilter(PurchasingSetting.auto_po_enabled, title="Auto PO")]
    form_columns = [
        "tenant",
        "auto_po_enabled",
        "auto_po_lookback_days",
        "auto_po_min_stock_trigger",
    ]

    async def on_model_change(
        self, data: dict, model: Any, is_created: bool, request: Request
    ) -> None:
        """Keep one PurchasingSetting per tenant (singleton semantics the
        API relies on)."""
        chosen = data.get("tenant")
        try:
            tenant_id = int(chosen)
        except (TypeError, ValueError):
            tenant_id = _selected_tenant_id(request)
        db = SessionLocal()
        try:
            existing = (
                db.query(PurchasingSetting)
                .filter(PurchasingSetting.tenant_id == tenant_id)
                .first()
            )
        finally:
            db.close()
        if existing and (is_created or existing.id != model.id):
            raise ValueError(
                "Purchasing automation settings already exist for the chosen "
                "tenant; edit the existing row instead."
            )
        if is_created:
            data["tenant"] = tenant_id
        await super().on_model_change(data, model, is_created, request)


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

    def is_visible(self, request: Request) -> bool:
        return False
