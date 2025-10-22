"""
Events API endpoints for event ingestion.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.logging import get_logger
from ...database.connection import get_db
from ...models.schemas import (
    EventsRequest, EventsResponse, ErrorResponse
)
from ...services.event_service import EventService
from ...core.deps import get_current_active_user
from ...models.database import User

logger = get_logger(__name__)

router = APIRouter(tags=["events"])


@router.post(
    "/events",
    response_model=EventsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest events",
    description="Accept batch of events for ingestion with idempotency support"
)
async def ingest_events(
    events_request: EventsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> EventsResponse:
    """
    Ingest a batch of events.
    
    - **events**: List of events to ingest (1-1000 events per request)
    - Supports idempotency - duplicate event_ids are safely ignored
    - Returns summary of processed events
    """
    try:
        event_service = EventService(db)
        
        logger.info(
            "Processing events batch",
            events_count=len(events_request.events)
        )
        
        # Debug: log first event details
        if events_request.events:
            first_event = events_request.events[0]
            logger.info(
                "First event details",
                event_id=str(first_event.event_id),
                user_id=first_event.user_id,
                event_type=first_event.event_type,
                properties_type=type(first_event.properties).__name__
            )
        
        responses, created_count, duplicate_count = await event_service.create_events(
            events_request.events
        )
        
        return EventsResponse(
            processed=len(responses),
            created=created_count,
            duplicates=duplicate_count,
            events=responses
        )
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        logger.error(
            "Failed to process events batch",
            error=str(e),
            events_count=len(events_request.events),
            traceback=error_trace
        )
        
        # Повертаємо детальну інформацію про помилку для діагностики
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process events: {str(e)}"
        )


@router.get(
    "/events",
    summary="Get events",
    description="Retrieve events with optional filtering and pagination"
)
async def get_events(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    from_date: Optional[datetime] = Query(None, description="Filter events from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter events to this date"),
    limit: int = Query(100, ge=1, le=1000, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get events with optional filtering and pagination.
    
    - **user_id**: Filter events for specific user
    - **event_type**: Filter events by type
    - **from_date**: Start date for filtering (ISO-8601)
    - **to_date**: End date for filtering (ISO-8601)
    - **limit**: Maximum number of events to return (1-1000)
    - **offset**: Number of events to skip for pagination
    """
    try:
        event_service = EventService(db)
        
        logger.info(
            "Retrieving events",
            user_id=user_id,
            event_type=event_type,
            from_date=from_date.isoformat() if from_date else None,
            to_date=to_date.isoformat() if to_date else None,
            limit=limit,
            offset=offset
        )
        
        events = await event_service.get_events(
            user_id=user_id,
            event_type=event_type,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        events_data = []
        for event in events:
            # Safely parse properties JSON
            properties = {}
            if event.properties:
                try:
                    if isinstance(event.properties, str):
                        import json
                        properties = json.loads(event.properties)
                    elif isinstance(event.properties, dict):
                        properties = event.properties
                except (json.JSONDecodeError, ValueError):
                    properties = {}
            
            events_data.append({
                "event_id": str(event.event_id),
                "occurred_at": event.occurred_at.isoformat(),
                "user_id": event.user_id,
                "event_type": event.event_type,
                "properties": properties,
                "created_at": event.created_at.isoformat()
            })
        
        return {
            "events": events_data,
            "count": len(events_data),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(
            "Failed to retrieve events",
            error=str(e),
            user_id=user_id,
            event_type=event_type
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve events"
        )


@router.get(
    "/events/health",
    summary="Health check",
    description="Simple health check of events endpoint"
)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "events"}
