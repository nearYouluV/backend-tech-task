"""
Event service for handling event ingestion and retrieval.
"""

import json
from datetime import datetime
from typing import List, Tuple, Union, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..models.database import Event
from ..models.schemas import EventInput, EventResponse

logger = get_logger(__name__)


class EventService:
    """Service for handling event operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_events(self, events: List[EventInput]) -> Tuple[List[EventResponse], int, int]:
        """
        Create multiple events with idempotency support.
        
        Returns:
            Tuple of (responses, created_count, duplicate_count)
        """
        responses = []
        created_count = 0
        duplicate_count = 0
        
        for event_data in events:
            try:
                # Check if event already exists
                result = await self.db.execute(
                    select(Event).filter(Event.event_id == event_data.event_id)
                )
                existing_event = result.scalar_one_or_none()
                
                if existing_event:
                    responses.append(EventResponse(
                        event_id=event_data.event_id,
                        status="duplicate"
                    ))
                    duplicate_count += 1
                    logger.info(
                        "Event already exists",
                        event_id=str(event_data.event_id),
                        user_id=event_data.user_id
                    )
                else:
                    # Create new event
                    db_event = Event(
                        event_id=event_data.event_id,
                        occurred_at=event_data.occurred_at,
                        user_id=event_data.user_id,
                        event_type=event_data.event_type,
                        properties=json.dumps(event_data.properties),
                        created_at=datetime.now()
                    )
                    
                    self.db.add(db_event)
                    
                    responses.append(EventResponse(
                        event_id=event_data.event_id,
                        status="created"
                    ))
                    created_count += 1
                    logger.info(
                        "Event created",
                        event_id=str(event_data.event_id),
                        user_id=event_data.user_id,
                        event_type=event_data.event_type
                    )
                    
            except IntegrityError as e:
                # Handle race conditions - event might have been created concurrently
                await self.db.rollback()
                responses.append(EventResponse(
                    event_id=event_data.event_id,
                    status="duplicate"
                ))
                duplicate_count += 1
                logger.warning(
                    "Event creation failed due to duplicate",
                    event_id=str(event_data.event_id),
                    error=str(e)
                )
            except Exception as e:
                await self.db.rollback()
                logger.error(
                    "Failed to create event",
                    event_id=str(event_data.event_id),
                    error=str(e)
                )
                raise
        
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to commit events", error=str(e))
            raise
        
        return responses, created_count, duplicate_count
    
    async def get_events(
        self, 
        user_id: Optional[int] = None,
        event_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Event]:
        """
        Get events with optional filtering and pagination.
        
        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            from_date: Filter events from this date (inclusive)
            to_date: Filter events to this date (inclusive)
            limit: Maximum number of events to return
            offset: Number of events to skip
        
        Returns:
            List of Event objects
        """
        query = select(Event)
        
        # Apply filters
        filters = []
        if user_id is not None:
            filters.append(Event.user_id == user_id)
        
        if event_type is not None:
            filters.append(Event.event_type == event_type)
        
        if from_date is not None:
            filters.append(Event.occurred_at >= from_date)
        
        if to_date is not None:
            filters.append(Event.occurred_at <= to_date)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Apply ordering, pagination
        query = (
            query
            .order_by(Event.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_event_by_id(self, event_id: UUID) -> Union[Event, None]:
        """Get event by ID."""
        result = await self.db.execute(
            select(Event).filter(Event.event_id == event_id)
        )
        return result.scalar_one_or_none()
    
    async def get_events_by_user(self, user_id: int, limit: int = 100) -> List[Event]:
        """Get events for a specific user."""
        result = await self.db.execute(
            select(Event)
            .filter(Event.user_id == user_id)
            .order_by(Event.occurred_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_events_by_type(self, event_type: str, limit: int = 100) -> List[Event]:
        """Get events by type."""
        result = await self.db.execute(
            select(Event)
            .filter(Event.event_type == event_type)
            .order_by(Event.occurred_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
