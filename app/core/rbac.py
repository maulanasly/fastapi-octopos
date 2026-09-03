DEFAULT_PERMISSION_DEFINITIONS: dict[str, str] = {
    "products:manage": "Manage products and categories",
    "customers:manage": "Manage customers",
    "customers:create": "Create customers",
    "promotions:manage": "Manage promotions and discounts",
    "orders:manage": "Create and manage orders",
    "payments:manage": "Add order payments",
    "refunds:view": "View refunds",
    "refunds:create": "Create refunds",
    "inventory:view": "View inventory movements and suggestions",
    "purchasing:manage": "Manage suppliers, purchase orders, and invoices",
    "purchasing:approve": "Approve or reject purchase invoices, orders, and supplier payments",
    "reports:view": "View analytics and summary reports",
    "taxes:read": "View tax rules",
    "taxes:manage": "Manage tax rules",
    "settings:manage": "Manage system settings and localization",
    "users:manage": "Manage staff (create, edit, deactivate)",
    "users:manage_roles": "Assign roles and manage RBAC",
    "orders:release_reservations": "Release expired reservations",
    "orders:track": "Track order trips and report service positions",
}

DEFAULT_ROLE_DEFINITIONS: dict[str, dict] = {
    "cashier": {
        "description": "POS cashier role",
        "is_system": True,
        "permissions": [
            "orders:manage",
            "payments:manage",
            "refunds:view",
            "refunds:create",
            "inventory:view",
            "taxes:read",
            "customers:create",
        ],
    },
    "manager": {
        "description": "Store manager role",
        "is_system": True,
        "permissions": [
            "products:manage",
            "customers:manage",
            "customers:create",
            "promotions:manage",
            "orders:manage",
            "payments:manage",
            "refunds:view",
            "refunds:create",
            "inventory:view",
            "purchasing:manage",
            "reports:view",
            "taxes:read",
            "taxes:manage",
            "settings:manage",
            "users:manage",
            "orders:release_reservations",
            "orders:track",
        ],
    },
    "service_agent": {
        "description": "Field service role (drive order trips, report position)",
        "is_system": True,
        "permissions": [
            "orders:track",
        ],
    },
    "admin": {
        "description": "System administrator role",
        "is_system": True,
        "permissions": list(DEFAULT_PERMISSION_DEFINITIONS.keys()),
    },
}


def ensure_rbac_defaults(db):
    from app.models.rbac import Permission, Role

    for code, description in DEFAULT_PERMISSION_DEFINITIONS.items():
        permission = db.query(Permission).filter(Permission.code == code).first()
        if not permission:
            db.add(Permission(code=code, description=description))
    db.flush()

    for role_name, role_config in DEFAULT_ROLE_DEFINITIONS.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(
                name=role_name,
                description=role_config["description"],
                is_system=role_config["is_system"],
            )
            db.add(role)
            db.flush()

        permission_codes = role_config["permissions"]
        role.permissions = (
            db.query(Permission).filter(Permission.code.in_(permission_codes)).all()
            if permission_codes
            else []
        )
        db.add(role)


def assign_default_cashier_role(db, user):
    from app.models.rbac import Role

    ensure_rbac_defaults(db)
    cashier_role = db.query(Role).filter(Role.name == "cashier").first()
    if cashier_role and all(role.id != cashier_role.id for role in user.roles):
        user.roles.append(cashier_role)
        db.add(user)


def assign_default_owner_role(db, user):
    """Grant the full admin role to a tenant's first (owner) user."""
    from app.models.rbac import Role

    ensure_rbac_defaults(db)
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if admin_role and all(role.id != admin_role.id for role in user.roles):
        user.roles.append(admin_role)
        db.add(user)
