"""Run-scoped replay evidence, ground truth, and process traces."""
import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base, JSONType


class DetectionProfile(Base):
    __tablename__ = 'detection_profiles'
    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False, default='')
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    snapshot = Column(JSONType, nullable=False)


class ExperimentRun(Base):
    __tablename__ = 'experiment_runs'
    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    seed = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default='queued', index=True)
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    snapshot = Column(JSONType, nullable=False)
    topology = Column(JSONType, nullable=False)
    metrics = Column(JSONType)
    verification = Column(JSONType)
    error = Column(String)


class ExperimentEvent(Base):
    __tablename__ = 'experiment_events'
    __table_args__ = (UniqueConstraint('run_id','position'),)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.event_id'), primary_key=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey('experiment_runs.run_id'), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    label = Column(String, nullable=False)
    expected_positive = Column(Boolean, nullable=False)
    expected_techniques = Column(JSONType, nullable=False)


class EventAlert(Base):
    __tablename__ = 'event_alerts'
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.event_id'), primary_key=True)
    alert_id = Column(UUID(as_uuid=True), ForeignKey('alerts.alert_id'), primary_key=True)


class ExperimentTrace(Base):
    __tablename__ = 'experiment_traces'
    __table_args__ = (UniqueConstraint('run_id','trace_key'),)
    trace_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey('experiment_runs.run_id'), nullable=False, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.event_id'))
    trace_key = Column(String, nullable=False)
    ordinal = Column(Integer, nullable=False)
    stage = Column(String, nullable=False)
    message = Column(String, nullable=False)
    payload = Column(JSONType, nullable=False, default=dict)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
