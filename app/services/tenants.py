import re

from sqlalchemy.orm import Session

from app.models.tenant import Tenant


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40]
    return slug or "business"


def create_tenant(db: Session, name: str = "Business") -> Tenant:
    """Create a tenant with a unique slug. Caller must flush/commit."""
    base = _slugify(name)
    slug = base
    counter = 1
    while db.query(Tenant.id).filter(Tenant.slug == slug).first():
        counter += 1
        slug = f"{base}-{counter}"
    tenant = Tenant(name=name, slug=slug, is_active=True)
    db.add(tenant)
    db.flush()
    return tenant
