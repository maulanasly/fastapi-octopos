from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, require_permissions
from app.core.audit import log_action
from app.core.database import get_db
from app.core.rbac import (
    DEFAULT_PERMISSION_DEFINITIONS,
    assign_default_cashier_role,
    ensure_rbac_defaults,
)
from app.models.rbac import Permission, Role
from app.models.user import User
from app.schemas.rbac import Role as RoleSchema
from app.schemas.rbac import (
    RoleCreate,
    RoleUpdate,
    UserPermissionsResponse,
    UserRoleAssign,
    UserRolesResponse,
)

router = APIRouter()


@router.post("/seed-defaults")
def seed_default_rbac(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage_roles")),
):
    _ = current_user
    ensure_rbac_defaults(db)
    db.commit()
    return {"ok": True}


@router.get("/roles", response_model=List[RoleSchema])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage_roles")),
):
    _ = current_user
    return db.query(Role).order_by(Role.id.asc()).all()


@router.post("/roles", response_model=RoleSchema)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage_roles")),
):
    _ = current_user
    existing = db.query(Role).filter(Role.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role name already exists")

    role = Role(name=payload.name, description=payload.description, is_system=False)
    db.add(role)
    db.flush()
    if payload.permission_codes:
        permissions = (
            db.query(Permission)
            .filter(Permission.code.in_(payload.permission_codes))
            .all()
        )
        missing = sorted(
            set(payload.permission_codes) - {item.code for item in permissions}
        )
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Permission code(s) not found: {', '.join(missing)}",
            )
        role.permissions = permissions
        db.add(role)
    log_action(
        db=db,
        action="rbac.role_create",
        user_id=current_user.id,
        resource_type="role",
        resource_id=role.id,
        details={"name": role.name, "permission_codes": payload.permission_codes},
    )
    db.commit()
    db.refresh(role)
    return role


@router.put("/roles/{role_id}", response_model=RoleSchema)
def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage_roles")),
):
    _ = current_user
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != role.name:
        duplicate = db.query(Role).filter(Role.name == update_data["name"]).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Role name already exists")

    permission_codes = update_data.pop("permission_codes", None)
    for field, value in update_data.items():
        setattr(role, field, value)

    if permission_codes is not None:
        permissions = (
            db.query(Permission).filter(Permission.code.in_(permission_codes)).all()
            if permission_codes
            else []
        )
        missing = sorted(set(permission_codes) - {item.code for item in permissions})
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Permission code(s) not found: {', '.join(missing)}",
            )
        role.permissions = permissions

    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.post("/users/{user_id}/roles", response_model=UserRolesResponse)
def assign_user_roles(
    user_id: int,
    payload: UserRoleAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage_roles")),
):
    _ = current_user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    roles = (
        db.query(Role).filter(Role.id.in_(payload.role_ids)).all()
        if payload.role_ids
        else []
    )
    missing = sorted(set(payload.role_ids) - {item.id for item in roles})
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Role id(s) not found: {', '.join(str(item) for item in missing)}",
        )

    user.roles = roles
    db.add(user)
    log_action(
        db=db,
        action="rbac.role_assign",
        user_id=current_user.id,
        resource_type="user",
        resource_id=user.id,
        details={"role_ids": payload.role_ids},
    )
    db.commit()
    db.refresh(user)
    return UserRolesResponse(user_id=user.id, roles=user.roles)


@router.get("/users/{user_id}/roles", response_model=UserRolesResponse)
def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage_roles")),
):
    _ = current_user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRolesResponse(user_id=user.id, roles=user.roles)


@router.get("/me/permissions", response_model=UserPermissionsResponse)
def get_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.is_superuser:
        return UserPermissionsResponse(
            user_id=current_user.id,
            permissions=sorted(DEFAULT_PERMISSION_DEFINITIONS.keys()),
        )

    permissions = sorted(
        {perm.code for role in current_user.roles for perm in role.permissions}
    )
    if not permissions:
        assign_default_cashier_role(db=db, user=current_user)
        db.commit()
        db.refresh(current_user)
        permissions = sorted(
            {perm.code for role in current_user.roles for perm in role.permissions}
        )

    return UserPermissionsResponse(user_id=current_user.id, permissions=permissions)
