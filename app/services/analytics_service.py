"""
Analytics service for generating statistics and reports.
"""

from datetime import datetime
from typing import List

from sqlalchemy import and_, func, distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..models.database import Event

logger = get_logger(__name__)


class AnalyticsService:
    """Service for analytics operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_basic_stats(self) -> dict:
        """Get basic event statistics."""
        # Total events
        total_result = await self.db.execute(select(func.count(Event.id)))
        total_events = total_result.scalar()
        
        # Unique users
        users_result = await self.db.execute(select(func.count(distinct(Event.user_id))))
        unique_users = users_result.scalar()
        
        # Event types
        types_result = await self.db.execute(select(func.count(distinct(Event.event_type))))
        event_types = types_result.scalar()
        
        logger.info(
            "Generated basic stats",
            total_events=total_events,
            unique_users=unique_users,
            event_types=event_types
        )
        
        return {
            "total_events": total_events,
            "unique_users": unique_users,
            "event_types_count": event_types
        }
    
    async def get_top_events(self, from_date: datetime = None, to_date: datetime = None, limit: int = 10) -> List[dict]:
        """Get top event types by count."""
        query = select(
            Event.event_type,
            func.count(Event.id).label('count')
        )
        
        # Add date filtering if provided
        if from_date and to_date:
            query = query.where(
                and_(
                    Event.occurred_at >= from_date,
                    Event.occurred_at <= to_date
                )
            )
        
        query = query.group_by(Event.event_type).order_by(func.count(Event.id).desc()).limit(limit)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        top_events = []
        for row in rows:
            top_events.append({
                "event_type": row.event_type,
                "count": row.count
            })
        
        logger.info(
            "Generated top events",
            limit=limit,
            records_count=len(top_events)
        )
        
        return top_events
    
    async def get_dau_stats(self, from_date: datetime, to_date: datetime) -> List[dict]:
        """Get Daily Active Users statistics."""
        query = select(
            func.date(Event.occurred_at).label('date'),
            func.count(distinct(Event.user_id)).label('unique_users')
        ).where(
            and_(
                Event.occurred_at >= from_date,
                Event.occurred_at <= to_date
            )
        ).group_by(func.date(Event.occurred_at)).order_by(func.date(Event.occurred_at))
        
        result = await self.db.execute(query)
        rows = result.all()
        
        dau_stats = []
        for row in rows:
            dau_stats.append({
                "date": str(row.date),
                "unique_users": row.unique_users
            })
        
        logger.info(
            "Generated DAU stats",
            from_date=from_date,
            to_date=to_date,
            records_count=len(dau_stats)
        )
        
        return dau_stats
    
    async def get_retention_stats(self, start_date: datetime, windows: int, period_type: str) -> List[dict]:
        """Get user retention statistics."""
        # This is a simplified implementation
        # In a real scenario, you'd want more complex retention analysis
        
        logger.info(
            "Generated retention stats",
            start_date=start_date,
            windows=windows,
            period_type=period_type
        )
        
        # Return empty data for now
        return []
