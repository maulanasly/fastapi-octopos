"""Admin relationship-column formatting: render human-readable labels
instead of raw SQLAlchemy object representations.

Each :class:`sqladmin.ModelView` that mixes in
:class:`LabeledRelationsMixin` gets its relationship columns (from
``column_list`` / ``column_details_list``) auto-formatted via
:data:`RELATION_LABELS`.
"""
from typing import Any, Callable, Dict, List, Tuple, Union

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import InstrumentedAttribute

from app.models.customer import Customer
from app.models.drawer import DrawerSession
from app.models.product import Category, Product
from app.models.promotion import Promotion
from app.models.purchase import PurchaseInvoice, PurchaseOrder, Supplier
from app.models.rbac import Permission, Role
from app.models.shift_reconciliation import ShiftReconciliation
from app.models.tax import TaxRule
from app.models.user import User

RelationLabelSpec = Union[Tuple[str, ...], Callable[[Any], str]]

RELATION_LABELS: Dict[type, RelationLabelSpec] = {
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
}


def _label(obj: Any) -> str:
    if obj is None:
        return "-"
    spec = RELATION_LABELS.get(type(obj))
    if spec is None:
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
    if isinstance(value, (list, set, tuple)):
        labels = [_label(item) for item in value]
        return [label for label in labels if label != "-"] or ["-"]
    return _label(value)


def _build_relation_formatters(
    model: type,
    columns: List[InstrumentedAttribute],
) -> Dict[InstrumentedAttribute, Callable[[Any, str], str]]:
    formatters = {}
    relation_names = set(sa_inspect(model).relationships.keys())
    for attr in columns:
        name = getattr(attr, "key", None)
        if name in relation_names:
            formatters[attr] = lambda obj, prop, _name=name: _render_relation(
                getattr(obj, _name)
            )
    return formatters


class LabeledRelationsMixin:
    """Mixin adding relationship-label formatting to a sqladmin ModelView.

    Sample usage::

        class OrderAdmin(LabeledRelationsMixin, ModelView, model=Order):
            column_list = [Order.id, Order.customer, Order.user]

    ``Order.customer`` renders as the customer name, ``Order.user`` as the
    user email, etc., instead of ``<Customer object at 0x...>``.
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
                **_build_relation_formatters(model, detail_columns + list_columns),
            }
        super().__init__(*args, **kwargs)
