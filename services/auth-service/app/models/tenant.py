from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..core.database import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan = Column(String(50), default="starter")
    status = Column(String(50), default="active")
    max_users = Column(Integer, default=10)
    max_api_calls_per_month = Column(Integer, default=10000)
    meta_info = Column('metadata', JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
