from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SyncEventLog(Base):
    __tablename__ = "sync_event_logs"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "client_event_id", "event_type", name="uq_sync_event_log_unique"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    client_event_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    idempotency_key = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, default="success", index=True)
    resource_type = Column(String, nullable=True)
    resource_id = Column(Integer, nullable=True)
    message = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
