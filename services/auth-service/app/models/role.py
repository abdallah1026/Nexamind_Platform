from sqlalchemy import Column, String, Boolean, JSON, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..core.database import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    permissions = Column(JSON, default=list)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
