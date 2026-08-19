"""Admin relationship formatting: render human-readable labels instead of
raw SQLAlchemy object representations.

Each :class:`sqladmin.ModelView` that mixes in
:class:`LabeledRelationsMixin` gets its relationship columns (from
``column_list`` / ``column_details_list``) auto-formatted via
:data:`RELATION_LABELS`. Editable views additionally use
:class:`LabeledFormConverter`, so relationship dropdowns in the create/edit
forms show the same labels instead of object reprs.
"""

from collections.abc import Callable
from typing import Any

import anyio

# pyrefly: ignore [missing-import]
from sqladmin.forms import ModelConverter
from sqladmin.helpers import is_async_session_maker
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute

from app.models.customer import Customer, LoyaltyTransaction
from app.models.drawer import DrawerSession
from app.models.order import Order, OrderItem
from app.models.payment import Payment
from app.models.product import Category, Product
from app.models.promotion import Promotion
from app.models.purchase import (
    PurchaseInvoice,
    PurchaseInvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)
from app.models.rbac import Permission, Role
from app.models.refund import Refund, RefundItem
from app.models.shift_reconciliation import ShiftReconciliation
from app.models.stock_movement import StockMovement
from app.models.tax import OrderTaxLine, TaxRule
from app.models.tenant import Tenant
from app.models.user import User

RelationLabelSpec = tuple[str, ...] | Callable[[Any], str]

RELATION_LABELS: dict[type, RelationLabelSpec] = {
    Tenant: ("name",),
    Product: ("name",),
    Category: ("name",),
    User: ("email",),
    Customer: ("name",),
    Supplier: ("name",),
    Promotion: ("code",),
    TaxRule: ("name",),
    Role: ("name",),
    Permission: ("code",),
    DrawerSession: lambda obj: f"Session #{obj.id}",
    PurchaseOrder: lambda obj: f"PO #{obj.id}",
    PurchaseInvoice: lambda obj: obj.invoice_number or f"Invoice #{obj.id}",
    ShiftReconciliation: lambda obj: f"Recon #{obj.id}",
    Order: lambda obj: f"Order #{obj.id}",
    OrderItem: lambda obj: f"Order Item #{obj.id}",
    StockMovement: lambda obj: f"Movement #{obj.id}",
    LoyaltyTransaction: lambda obj: f"Loyalty #{obj.id}",
    OrderTaxLine: lambda obj: f"Tax Line #{obj.id}",
    Payment: lambda obj: f"Payment #{obj.id}",
    Refund: lambda obj: f"Refund #{obj.id}",
    RefundItem: lambda obj: f"Refund Item #{obj.id}",
    PurchaseOrderItem: lambda obj: f"PO Item #{obj.id}",
    PurchaseInvoiceItem: lambda obj: f"Invoice Item #{obj.id}",
}


def _label(obj: Any) -> str:
    if obj is None:
        return "-"
    spec = RELATION_LABELS.get(type(obj))
    if spec is None:
        # Fall back to a readable "<Type> #<id>" instead of leaking the
        # default object repr ("<Type object at 0x...>").
        obj_id = getattr(obj, "id", None)
        if obj_id is not None:
            return f"{type(obj).__name__} #{obj_id}"
        return str(obj)
    if callable(spec):
        return spec(obj)
    value = obj
    for part in spec:
        value = getattr(value, part, None)
        if value is None:
            return "-"
    return value


def _render_relation(value: Any) -> Any:
    """Label a relation for sqladmin.

    Scalar relations return a label string; to-many relations return a
    *list* of labels, because sqladmin's list/details templates zip the
    related objects against the formatted values element-wise.
    """
    if value is None:
        return "-"
    if isinstance(value, list | set | tuple):
        labels = [_label(item) for item in value]
        return [label for label in labels if label != "-"] or ["-"]
    return _label(value)


def _make_relation_formatter(name: str) -> Callable[[Any, str], str]:
    # sqladmin 0.31 introspects formatter signatures and passes `request`
    # when a third parameter exists; keep the signature exactly (obj, prop).
    def fmt(obj, prop):
        return _render_relation(getattr(obj, name))

    return fmt


def _build_relation_formatters(
    model: type,
    columns: list[InstrumentedAttribute],
) -> dict[InstrumentedAttribute, Callable[[Any, str], str]]:
    formatters = {}
    relation_names = set(sa_inspect(model).relationships.keys())
    for attr in columns:
        name = getattr(attr, "key", None)
        if name in relation_names:
            formatters[attr] = _make_relation_formatter(name)
    return formatters


def _all_relation_attributes(model: type) -> list[InstrumentedAttribute]:
    """Return every relationship attribute of *model*.

    sqladmin's detail page renders *all* model attributes by default (see
    ``ModelView.get_details_columns``), not just ``column_list``, so any
    relationship outside those lists would otherwise fall through to the raw
    ``str(obj)`` representation.
    """
    return [getattr(model, name) for name in sa_inspect(model).relationships.keys()]


class LabeledFormConverter(ModelConverter):
    """sqladmin form converter rendering relationship dropdown labels from
    :data:`RELATION_LABELS` instead of raw ``str(obj)`` representations.
    """

    async def _prepare_select_options(self, prop, session_maker):
        target_model = prop.mapper.class_
        stmt = select(target_model)

        if is_async_session_maker(session_maker):
            async with session_maker() as session:
                objects = await session.execute(stmt)
                return [
                    (str(self._get_identifier_value(obj)), _label(obj))
                    for obj in objects.scalars().unique().all()
                ]
        else:
            with session_maker() as session:
                objects = await anyio.to_thread.run_sync(session.execute, stmt)
                return [
                    (str(self._get_identifier_value(obj)), _label(obj))
                    for obj in objects.scalars().unique().all()
                ]


class LabeledRelationsMixin:
    """Mixin adding relationship-label formatting to a sqladmin ModelView.

    Sample usage::

        class OrderAdmin(LabeledRelationsMixin, ModelView, model=Order):
            column_list = [Order.id, Order.customer, Order.user]

    ``Order.customer`` renders as the customer name, ``Order.user`` as the
    user email, etc., instead of ``<Customer object at 0x...>``.

    Editable views (``can_create`` or ``can_edit``) also get
    :class:`LabeledFormConverter` so relationship selects in the create/edit
    forms render labels instead of object reprs.
    """

    def __init__(self, *args, **kwargs):
        model = getattr(self, "model", None)
        if model is not None:
            list_columns = list(getattr(self, "column_list", []) or [])
            detail_columns = list(getattr(self, "column_details_list", []) or [])
            self.column_formatters = {
                **dict(getattr(self, "column_formatters", {}) or {}),
                **_build_relation_formatters(model, list_columns + detail_columns),
            }
            self.column_formatters_detail = {
                **dict(getattr(self, "column_formatters_detail", {}) or {}),
                **_build_relation_formatters(
                    model, detail_columns + _all_relation_attributes(model)
                ),
            }
            if getattr(self, "can_create", True) or getattr(self, "can_edit", True):
                self.form_converter = LabeledFormConverter
        super().__init__(*args, **kwargs)
