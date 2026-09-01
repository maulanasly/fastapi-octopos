# pyrefly: ignore [missing-import]
from sqladmin import ModelView
from sqladmin.filters import BooleanFilter

# pyrefly: ignore [missing-import]
from starlette.requests import Request

from app.admin.base import TenantScopedModelView
from app.admin.formatting import LabeledRelationsMixin
from app.admin.password_field import AdminPasswordField
from app.core.security import get_password_hash
from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.models.user import User


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

    column_filters = [BooleanFilter(User.is_active, title="Active")]
    column_labels = {
        User.hashed_password: "Password",
        User.is_active: "Active",
        User.email: "Email",
    }
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

    def is_visible(self, request: Request) -> bool:
        return False


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

    def is_visible(self, request: Request) -> bool:
        return False


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

    def is_visible(self, request: Request) -> bool:
        return False
