import uuid
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base, JSONType

class Host(Base):
    __tablename__ = "hosts"

    host_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_name = Column(String, nullable=False)
    os_name = Column(String)
    os_version = Column(String)
    agent_type = Column(String)
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    tags = Column(JSONType, server_default='{}')
    criticality = Column(Integer, default=1)
