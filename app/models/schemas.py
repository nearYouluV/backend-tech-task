"""
Pydantic models for API requests and responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


class EventInput(BaseModel):
    """Model for incoming event data."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "occurred_at": "2025-08-21T06:52:34+03:00",
                "user_id": 1,
                "event_type": "view_item",
                "properties": {
                    "country": "PL",
                    "session_id": "5ef18783",
                    "item_id": "SKU6991",
                    "price": 118.64,
                    "currency": "USD"
                }
            }
        }
    )
    
    event_id: UUID = Field(..., description="Unique event identifier")
    occurred_at: datetime = Field(..., description="When the event occurred (ISO-8601)")
    user_id: int = Field(..., description="User identifier", gt=0)
    event_type: str = Field(..., description="Type of event", min_length=1, max_length=100)
    properties: Dict[str, Any] = Field(default_factory=dict, description="Event properties as JSON object")


class EventsRequest(BaseModel):
    """Model for batch event ingestion."""
    
    events: List[EventInput] = Field(..., description="List of events", min_length=1, max_length=1000)


class EventResponse(BaseModel):
    """Model for event response."""
    
    event_id: UUID
    status: str = Field(description="Processing status: 'created' or 'duplicate'")


class EventsResponse(BaseModel):
    """Model for batch events response."""
    
    processed: int = Field(description="Number of processed events")
    created: int = Field(description="Number of newly created events")
    duplicates: int = Field(description="Number of duplicate events (idempotent)")
    events: List[EventResponse] = Field(description="Individual event results")


class DAUStats(BaseModel):
    """Model for Daily Active Users statistics."""
    
    date: str = Field(description="Date in YYYY-MM-DD format")
    unique_users: int = Field(description="Number of unique users", ge=0)


class DAUResponse(BaseModel):
    """Response model for DAU statistics."""
    
    from_date: str = Field(description="Start date")
    to_date: str = Field(description="End date") 
    data: List[DAUStats] = Field(description="Daily statistics")


class TopEventStats(BaseModel):
    """Model for top event statistics."""
    
    event_type: str = Field(description="Event type")
    count: int = Field(description="Number of occurrences", ge=0)


class TopEventsResponse(BaseModel):
    """Response model for top events statistics."""
    
    from_date: str = Field(description="Start date")
    to_date: str = Field(description="End date")
    limit: int = Field(description="Limit parameter")
    data: List[TopEventStats] = Field(description="Top events statistics")


class RetentionCohort(BaseModel):
    """Model for retention cohort data."""
    
    cohort_date: str = Field(description="Cohort start date")
    cohort_size: int = Field(description="Initial cohort size", ge=0)
    periods: List[int] = Field(description="Retention counts for each period")


class RetentionResponse(BaseModel):
    """Response model for retention analysis."""
    
    start_date: str = Field(description="Analysis start date")
    windows: int = Field(description="Number of periods to analyze")
    period_type: str = Field(description="Period type: 'daily' or 'weekly'")
    data: List[RetentionCohort] = Field(description="Cohort retention data")


class ErrorResponse(BaseModel):
    """Model for error responses."""
    
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
