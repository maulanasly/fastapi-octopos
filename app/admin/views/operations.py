# pyrefly: ignore [missing-import]
from sqladmin.filters import AllUniqueStringValuesFilter, ForeignKeyFilter

from app.admin.base import TenantScopedModelView
from app.admin.formatting import LabeledRelationsMixin
from app.models.drawer import DrawerSession
from app.models.shift_reconciliation import ShiftReconciliation
from app.models.user import User


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
