from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_superuser
from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogEntry, AuditLogList

router = APIRouter()


@router.get("/logs", response_model=AuditLogList)
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    action: Optional[str] = Query(None, description="Filter by action name"),
    user_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 100,
):
    """Audit trail of sensitive operations. Superuser only."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    total = query.count()
    items = query.order_by(AuditLog.id.desc()).offset(skip).limit(limit).all()
    return AuditLogList(total=total, items=items)
