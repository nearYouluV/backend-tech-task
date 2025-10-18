import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Column, DateTime, Integer, String, Text, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.types import TypeDecorator, VARCHAR

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type."""
    
    impl = VARCHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PGUUID())
        else:
            return dialect.type_descriptor(VARCHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, str):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, UUID):
                return UUID(value)
            return value


class Event(Base):
    """Event model for storing ingested events."""
    
    __tablename__ = "events"
    
    # Primary key - auto-incrementing ID
    id = Column(Integer, primary_key=True, index=True)
    
    # Event data
    event_id = Column(GUID, unique=True, nullable=False, index=True)
    occurred_at = Column(DateTime, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    properties = Column(Text, nullable=False)  # JSON string
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_user_occurred', 'user_id', 'occurred_at'),
        Index('idx_event_type_occurred', 'event_type', 'occurred_at'),
        Index('idx_occurred_at_date', 'occurred_at'),
    )
    
    def __repr__(self):
        return f"<Event(event_id={self.event_id}, event_type={self.event_type}, user_id={self.user_id})>"
    
    @property
    def properties_dict(self):
        """Return properties as dictionary."""
        try:
            return json.loads(self.properties) if self.properties else {}
        except json.JSONDecodeError:
            return {}
    
    @properties_dict.setter
    def properties_dict(self, value):
        """Set properties from dictionary."""
        self.properties = json.dumps(value) if value else "{}"
