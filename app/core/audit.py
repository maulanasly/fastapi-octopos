"""Audit trail helper.

Records user actions on sensitive operations (refunds, stock adjustments,
drawer reconciliation, RBAC changes) into the ``audit_logs`` table.
Sensitive modules are RBAC-gated; the audit log is the permanent record
of who did what, complementing the product-level StockMovement ledger.
"""
import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.observability import get_request_id
from app.models.audit_log import AuditLog
from app.models.user import User


def log_action(
    db: Session,
    *,
    action: str,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Append an audit entry (does not commit; caller controls the commit)."""
    tenant_id = None
    if user_id is not None:
        tenant_id = db.query(User.tenant_id).filter(User.id == user_id).scalar()
    entry = AuditLog(
        user_id=user_id,
        tenant_id=tenant_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details_json=json.dumps(details, default=str) if details else None,
        ip_address=ip_address,
        request_id=get_request_id(),
    )
    db.add(entry)
    return entry
