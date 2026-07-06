"""Shared validation helpers for endpoints."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.drawer import DrawerSession
from app.models.order import Order


def validate_drawer_session_status(
    db: Session, order: Order, action: str = "perform this action"
) -> None:
    """Validate that the drawer session for an order is still open.

    Args:
        db: Database session
        order: Order to validate
        action: Action description for error message (e.g., "add payment", "refund")
    """
    if order.drawer_session_id:
        drawer = (
            db.query(DrawerSession)
            .filter(DrawerSession.id == order.drawer_session_id)
            .first()
        )
        if drawer and drawer.status != "open":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot {action} on an order from a closed drawer session",
            )
