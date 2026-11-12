"""Durable processing state and defense audit records shared by API and workers."""
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base, JSONType


class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.event_id"), primary_key=True)
    status = Column(String, nullable=False, default="pending", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    error = Column(String, nullable=True)
    twin_status = Column(String, nullable=False, default="pending", index=True)
    twin_attempts = Column(Integer, nullable=False, default=0)
    twin_error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)


class ResponseAction(Base):
    __tablename__ = "response_actions"
    __table_args__ = (UniqueConstraint("incident_id", "policy_id", "action"),)
    action_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.incident_id"), nullable=False, index=True)
    policy_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    autonomy = Column(String, nullable=False)
    status = Column(String, nullable=False, default="proposed")
    requested_by = Column(String, ForeignKey("users.id"), nullable=False)
    result = Column(JSONType, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    executed_at = Column(DateTime(timezone=True), nullable=True)


class IntegrationSetting(Base):
    __tablename__ = "integration_settings"
    name = Column(String, primary_key=True)
    encrypted_value = Column(String, nullable=False)
