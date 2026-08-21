from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        # Email is unique per tenant (same staff email may exist in other
        # tenants). Superusers have tenant_id NULL; PG treats NULLs as
        # distinct, so superuser emails never conflict here.
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id"), nullable=True, index=True
    )  # NULL = platform superuser
    email = Column(String, index=True, nullable=False)
    hashed_password = Column(
        String, nullable=True
    )  # nullable for google auth only users
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    region = Column(String, nullable=True)  # regional preset: US | ID | None
    tenant = relationship("Tenant")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
