from sqlalchemy import Column, String, Integer, JSON, DateTime, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class AgentConversation(Base):
    __tablename__ = "agent_conversations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True))
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    agent_name = Column(String(100))
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default=dict)
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AgentSession(Base):
    __tablename__ = "agent_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True))
    agent_name = Column(String(100))
    status = Column(String(50), default="active")
    context = Column(JSON, default=dict)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
