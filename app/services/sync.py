"""Pull-side sync: catalog delta and event status for offline terminals."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.product import Category, Product
from app.models.promotion import Promotion
from app.models.sync_event import SyncEventLog
from app.models.tax import TaxRule


def get_catalog_delta(
    db: Session,
    since: Optional[datetime],
) -> dict:
    """Return catalog rows whose updated_at is newer than ``since``.

    Without ``since`` the full catalog is returned (first-time sync).
    ``server_time`` lets terminals clock-skew-adjust their watermark.
    """
    # SQLite stores naive datetimes; normalize the watermark to match.
    if since is not None and since.tzinfo is not None:
        since = since.astimezone(timezone.utc).replace(tzinfo=None)

    if since is None:
        categories = db.query(Category).all()
        products = db.query(Product).all()
        promotions = db.query(Promotion).all()
        tax_rules = db.query(TaxRule).filter(TaxRule.is_active.is_(True)).all()
    else:
        categories = db.query(Category).filter(Category.updated_at > since).all()
        products = db.query(Product).filter(Product.updated_at > since).all()
        promotions = db.query(Promotion).filter(Promotion.updated_at > since).all()
        tax_rules = (
            db.query(TaxRule)
            .filter(TaxRule.updated_at > since, TaxRule.is_active.is_(True))
            .all()
        )

    return {
        "server_time": datetime.now(timezone.utc),
        "since": since,
        "categories": categories,
        "products": products,
        "promotions": promotions,
        "tax_rules": tax_rules,
    }


def get_event_logs(
    db: Session,
    user_id: Optional[int],
    status: Optional[str],
    skip: int,
    limit: int,
) -> dict:
    """Paginated view of a terminal's processed offline events."""
    query = db.query(SyncEventLog)
    if user_id is not None:
        query = query.filter(SyncEventLog.user_id == user_id)
    if status:
        query = query.filter(SyncEventLog.status == status)
    total = query.count()
    items = query.order_by(SyncEventLog.id.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}
