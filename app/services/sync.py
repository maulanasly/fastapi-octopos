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
    tenant_id: int,
) -> dict:
    """Return catalog rows whose updated_at is newer than ``since``.

    Without ``since`` the full catalog is returned (first-time sync).
    ``server_time`` lets terminals clock-skew-adjust their watermark.
    """
    # Normalize the watermark to aware-UTC. Legacy SQLite stores naive
    # datetimes, so strip the tzinfo there to keep string comparisons valid.
    if since is not None:
        since = since.astimezone(timezone.utc)
        if db.bind.dialect.name == "sqlite":
            since = since.replace(tzinfo=None)

    if since is None:
        categories = db.query(Category).filter(Category.tenant_id == tenant_id).all()
        products = db.query(Product).filter(Product.tenant_id == tenant_id).all()
        promotions = db.query(Promotion).filter(Promotion.tenant_id == tenant_id).all()
        tax_rules = (
            db.query(TaxRule)
            .filter(TaxRule.is_active.is_(True), TaxRule.tenant_id == tenant_id)
            .all()
        )
    else:
        categories = (
            db.query(Category)
            .filter(Category.updated_at > since, Category.tenant_id == tenant_id)
            .all()
        )
        products = (
            db.query(Product)
            .filter(Product.updated_at > since, Product.tenant_id == tenant_id)
            .all()
        )
        promotions = (
            db.query(Promotion)
            .filter(Promotion.updated_at > since, Promotion.tenant_id == tenant_id)
            .all()
        )
        tax_rules = (
            db.query(TaxRule)
            .filter(
                TaxRule.updated_at > since,
                TaxRule.is_active.is_(True),
                TaxRule.tenant_id == tenant_id,
            )
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
    tenant_id: int,
) -> dict:
    """Paginated view of a terminal's processed offline events."""
    query = db.query(SyncEventLog).filter(SyncEventLog.tenant_id == tenant_id)
    if user_id is not None:
        query = query.filter(SyncEventLog.user_id == user_id)
    if status:
        query = query.filter(SyncEventLog.status == status)
    total = query.count()
    items = query.order_by(SyncEventLog.id.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}
