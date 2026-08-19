from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_permissions
from app.core.database import get_db
from app.core.rbac import assign_default_cashier_role
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import User as UserSchema
from app.schemas.user import UserCreate, UserUpdate

router = APIRouter()


def _ensure_same_tenant(target: User, current_user: User) -> None:
    """Superusers may manage any tenant's staff; tenant users only their own."""
    if current_user.is_superuser:
        return
    if target.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=403, detail="Cannot manage staff outside your tenant"
        ) from None


@router.get("/", response_model=list[UserSchema])
def get_users(
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage")),
):
    """List staff. Tenant admins see their own tenant; superusers may filter."""
    query = db.query(User)
    if current_user.is_superuser:
        if tenant_id is not None:
            query = query.filter(User.tenant_id == tenant_id)
    else:
        query = query.filter(User.tenant_id == current_user.tenant_id)
    return query.order_by(User.id.asc()).all()


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_staff_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage")),
):
    """Create a staff member in the tenant. Superusers must pass ``tenant_id``."""
    tenant_id = (
        payload.tenant_id if current_user.is_superuser else current_user.tenant_id
    )
    if tenant_id is None:
        raise HTTPException(
            status_code=400, detail="tenant_id is required when creating staff"
        ) from None

    same_tenant = (
        db.query(User)
        .filter(User.email == payload.email, User.tenant_id == tenant_id)
        .first()
    )
    superuser = (
        db.query(User)
        .filter(User.email == payload.email, User.tenant_id.is_(None))
        .first()
    )
    if same_tenant or superuser:
        raise HTTPException(
            status_code=400, detail="Email already registered"
        ) from None

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        is_active=payload.is_active,
        is_superuser=False,  # superuser promotion stays with the admin panel
        tenant_id=tenant_id,
    )
    db.add(user)
    assign_default_cashier_role(db=db, user=user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserSchema)
def update_staff_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage")),
):
    """Update a staff member (name, active flag, password reset)."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found") from None
    _ensure_same_tenant(target, current_user)

    if target.id == current_user.id and payload.is_active is False:
        raise HTTPException(
            status_code=400, detail="You cannot deactivate your own account"
        ) from None

    update_data = payload.model_dump(exclude_unset=True)
    if "email" in update_data and update_data["email"] != target.email:
        duplicate = (
            db.query(User)
            .filter(
                User.email == update_data["email"], User.tenant_id == target.tenant_id
            )
            .first()
        )
        if duplicate:
            raise HTTPException(
                status_code=400, detail="Email already registered"
            ) from None

    password = update_data.pop("password", None)
    if password is not None:
        target.hashed_password = get_password_hash(password)
    for field, value in update_data.items():
        setattr(target, field, value)

    db.add(target)
    db.commit()
    db.refresh(target)
    return target
