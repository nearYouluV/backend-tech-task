"""
SQLAlchemy database models.
"""

import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Column, DateTime, Integer, String, Text, Index, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.sql import func

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


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RefreshToken(Base):
    """Refresh token model for JWT authentication."""
    
    __tablename__ = "refresh_tokens"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Index for cleanup of expired tokens
    __table_args__ = (
        Index('idx_refresh_tokens_expires', 'expires_at'),
        Index('idx_refresh_tokens_user', 'user_id'),
    )


class Event(Base):
    """Event model for storing analytics events."""
    
    __tablename__ = "events"
    
    # Core fields
    event_id = Column(GUID, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    properties = Column(JSONB, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_events_user_occurred', 'user_id', 'occurred_at'),
        Index('idx_events_type_occurred', 'event_type', 'occurred_at'),
        Index('idx_events_occurred_at', 'occurred_at'),
    )
    
    @property
    def properties_dict(self):
        """Return properties as dict, handling both dict and JSON string."""
        if isinstance(self.properties, dict):
            return self.properties
        elif isinstance(self.properties, str):
            try:
                return json.loads(self.properties)
            except (json.JSONDecodeError, TypeError):
                return {}
        return self.properties or {}
    
    @properties_dict.setter 
    def properties_dict(self, value):
        """Set properties from dict."""
        self.properties = value
    
    def __repr__(self):
        return f"<Event(id={self.event_id}, user={self.user_id}, type={self.event_type})>"