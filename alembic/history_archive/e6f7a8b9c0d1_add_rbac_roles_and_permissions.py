"""add_rbac_roles_and_permissions

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a7b8c9
Create Date: 2026-05-28 05:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e6f7a8b9c0d1"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PERMISSIONS = {
    "products:manage": "Manage products and categories",
    "orders:manage": "Create and manage orders",
    "payments:manage": "Add order payments",
    "refunds:view": "View refunds",
    "refunds:create": "Create refunds",
    "inventory:view": "View inventory movements and suggestions",
    "purchasing:manage": "Manage suppliers, purchase orders, and invoices",
    "purchasing:approve": "Approve or reject purchase invoices",
    "reports:view": "View analytics and summary reports",
    "taxes:read": "View tax rules",
    "taxes:manage": "Manage tax rules",
    "settings:manage": "Manage system settings and localization",
    "users:manage_roles": "Assign roles and manage RBAC",
    "orders:release_reservations": "Release expired reservations",
}

ROLE_PERMISSIONS = {
    "cashier": [
        "orders:manage",
        "payments:manage",
        "refunds:view",
        "refunds:create",
        "inventory:view",
        "taxes:read",
    ],
    "manager": [
        "products:manage",
        "orders:manage",
        "payments:manage",
        "refunds:view",
        "refunds:create",
        "inventory:view",
        "purchasing:manage",
        "purchasing:approve",
        "reports:view",
        "taxes:read",
        "taxes:manage",
        "settings:manage",
        "orders:release_reservations",
    ],
    "admin": list(PERMISSIONS.keys()),
}


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("roles"):
        op.create_table(
            "roles",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column(
                "is_system", sa.Boolean(), nullable=False, server_default=sa.false()
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)
        op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    if not inspector.has_table("permissions"):
        op.create_table(
            "permissions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_permissions_id"), "permissions", ["id"], unique=False)
        op.create_index(
            op.f("ix_permissions_code"), "permissions", ["code"], unique=True
        )

    if not inspector.has_table("user_roles"):
        op.create_table(
            "user_roles",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("role_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id", "role_id", name="uq_user_roles_user_id_role_id"
            ),
        )
        op.create_index(op.f("ix_user_roles_id"), "user_roles", ["id"], unique=False)
        op.create_index(
            op.f("ix_user_roles_user_id"), "user_roles", ["user_id"], unique=False
        )
        op.create_index(
            op.f("ix_user_roles_role_id"), "user_roles", ["role_id"], unique=False
        )

    if not inspector.has_table("role_permissions"):
        op.create_table(
            "role_permissions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("role_id", sa.Integer(), nullable=False),
            sa.Column("permission_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"]),
            sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "role_id",
                "permission_id",
                name="uq_role_permissions_role_id_permission_id",
            ),
        )
        op.create_index(
            op.f("ix_role_permissions_id"), "role_permissions", ["id"], unique=False
        )
        op.create_index(
            op.f("ix_role_permissions_role_id"),
            "role_permissions",
            ["role_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_role_permissions_permission_id"),
            "role_permissions",
            ["permission_id"],
            unique=False,
        )

    for code, description in PERMISSIONS.items():
        permission_row = bind.execute(
            sa.text("SELECT id FROM permissions WHERE code = :code"),
            {"code": code},
        ).first()
        if not permission_row:
            bind.execute(
                sa.text(
                    "INSERT INTO permissions (code, description) VALUES (:code, :description)"
                ),
                {"code": code, "description": description},
            )

    for role_name in ("cashier", "manager", "admin"):
        role_row = bind.execute(
            sa.text("SELECT id FROM roles WHERE name = :name"),
            {"name": role_name},
        ).first()
        if not role_row:
            bind.execute(
                sa.text(
                    "INSERT INTO roles (name, description, is_system) "
                    "VALUES (:name, :description, :is_system)"
                ),
                {
                    "name": role_name,
                    "description": f"System role: {role_name}",
                    "is_system": True,
                },
            )

    role_ids = {
        row[1]: row[0]
        for row in bind.execute(sa.text("SELECT id, name FROM roles")).all()
    }
    permission_ids = {
        row[1]: row[0]
        for row in bind.execute(sa.text("SELECT id, code FROM permissions")).all()
    }

    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role_id = role_ids.get(role_name)
        if not role_id:
            continue
        for permission_code in permission_codes:
            permission_id = permission_ids.get(permission_code)
            if not permission_id:
                continue
            existing = bind.execute(
                sa.text(
                    "SELECT id FROM role_permissions "
                    "WHERE role_id = :role_id AND permission_id = :permission_id"
                ),
                {"role_id": role_id, "permission_id": permission_id},
            ).first()
            if not existing:
                bind.execute(
                    sa.text(
                        "INSERT INTO role_permissions (role_id, permission_id) "
                        "VALUES (:role_id, :permission_id)"
                    ),
                    {"role_id": role_id, "permission_id": permission_id},
                )

    admin_role_id = role_ids.get("admin")
    cashier_role_id = role_ids.get("cashier")

    if admin_role_id:
        superusers = bind.execute(
            sa.text("SELECT id FROM users WHERE is_superuser = 1")
        ).all()
        for row in superusers:
            user_id = row[0]
            existing = bind.execute(
                sa.text(
                    "SELECT id FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"
                ),
                {"user_id": user_id, "role_id": admin_role_id},
            ).first()
            if not existing:
                bind.execute(
                    sa.text(
                        "INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"
                    ),
                    {"user_id": user_id, "role_id": admin_role_id},
                )

    if cashier_role_id:
        users_without_role = bind.execute(
            sa.text(
                "SELECT u.id FROM users u "
                "LEFT JOIN user_roles ur ON ur.user_id = u.id "
                "WHERE ur.id IS NULL"
            )
        ).all()
        for row in users_without_role:
            user_id = row[0]
            bind.execute(
                sa.text(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"
                ),
                {"user_id": user_id, "role_id": cashier_role_id},
            )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("role_permissions"):
        op.drop_index(
            op.f("ix_role_permissions_permission_id"),
            table_name="role_permissions",
        )
        op.drop_index(
            op.f("ix_role_permissions_role_id"), table_name="role_permissions"
        )
        op.drop_index(op.f("ix_role_permissions_id"), table_name="role_permissions")
        op.drop_table("role_permissions")

    if inspector.has_table("user_roles"):
        op.drop_index(op.f("ix_user_roles_role_id"), table_name="user_roles")
        op.drop_index(op.f("ix_user_roles_user_id"), table_name="user_roles")
        op.drop_index(op.f("ix_user_roles_id"), table_name="user_roles")
        op.drop_table("user_roles")

    if inspector.has_table("permissions"):
        op.drop_index(op.f("ix_permissions_code"), table_name="permissions")
        op.drop_index(op.f("ix_permissions_id"), table_name="permissions")
        op.drop_table("permissions")

    if inspector.has_table("roles"):
        op.drop_index(op.f("ix_roles_name"), table_name="roles")
        op.drop_index(op.f("ix_roles_id"), table_name="roles")
        op.drop_table("roles")
