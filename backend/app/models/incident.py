import uuid
from sqlalchemy import Index, Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base, JSONType

class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        Index('ix_incidents_host_status_last_seen', 'host_id', 'status', 'last_seen'),
    )

    incident_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False, default="low")
    confidence = Column(Integer, nullable=False, default=50)
    status = Column(String, nullable=False, default="open")
    host_id = Column(UUID(as_uuid=True), ForeignKey("hosts.host_id"), nullable=True)
    first_seen = Column(DateTime(timezone=True), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=False)
    attack_story = Column(JSONType, server_default='[]')
    mitre_techniques = Column(JSONType, server_default='[]')
    assignee_id = Column(String, ForeignKey("users.id"), nullable=True)
    notes = Column(JSONType, server_default='[]')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Alerts relationship
    alerts = relationship("Alert", backref="incident", cascade="all, delete-orphan")
