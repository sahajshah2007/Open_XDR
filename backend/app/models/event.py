import uuid
from sqlalchemy import Index, Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base, JSONType

class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index('ix_events_timestamp', 'timestamp'),
        Index('ix_events_host_timestamp', 'host_id', 'timestamp'),
    )

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_id = Column(UUID(as_uuid=True), ForeignKey("hosts.host_id"))
    source = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    normalized = Column(JSONType, nullable=False)
    raw = Column(JSONType, nullable=False)
