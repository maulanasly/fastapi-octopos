from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_superuser
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema

router = APIRouter()


@router.get("/", response_model=list[UserSchema])
def get_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
):
    """List users (for role assignment). Superuser only."""
    return db.query(User).order_by(User.id.asc()).offset(skip).limit(limit).all()
