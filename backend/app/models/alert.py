import uuid
from sqlalchemy import Index, Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
from app.core.database import Base, JSONType

class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index('ix_alerts_incident_timestamp', 'incident_id', 'timestamp'),
        Index('ix_alerts_source_timestamp', 'source_ip', 'timestamp'),
    )

    alert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.incident_id"), nullable=True)
    host_id = Column(UUID(as_uuid=True), ForeignKey("hosts.host_id"), nullable=True)
    rule_id = Column(String, nullable=False)
    rule_name = Column(String, nullable=False)
    source = Column(String, nullable=True)  # Data source that generated this alert (wazuh, suricata, zeek)
    severity = Column(String, nullable=False)
    confidence = Column(String, nullable=True)
    mitre_tactic = Column(String, nullable=True)
    mitre_technique = Column(String, nullable=True)
    source_ip = Column(String, nullable=True)  # Using String instead of INET for SQLite compatibility in tests
    destination_ip = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    raw_event = Column(JSONType, nullable=False)
    enrichment = Column(JSONType, server_default='{}')
