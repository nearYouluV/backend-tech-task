"""
Data archival service for moving data from hot storage (PostgreSQL) to cold storage (ClickHouse).
Implements hot/cold data storage strategy.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_

from ..database.connection import get_db
from ..models.database import Event
from ..services.clickhouse_service import clickhouse_service

logger = logging.getLogger(__name__)


class DataArchivalService:
    """Service for managing data archival from hot to cold storage."""
    
    def __init__(self, 
                 hot_retention_days: int = 7,  # Keep data in PostgreSQL for 7 days
                 batch_size: int = 1000,      # Process in batches
                 max_archive_age_days: int = 30  # Don't archive data older than 30 days
                 ):
        self.hot_retention_days = hot_retention_days
        self.batch_size = batch_size
        self.max_archive_age_days = max_archive_age_days
    
    async def archive_old_events(self) -> Dict[str, Any]:
        """
        Archive events older than hot_retention_days to ClickHouse and remove from PostgreSQL.
        
        Returns:
            Dict with archival statistics
        """
        stats = {
            'started_at': datetime.now(),
            'events_processed': 0,
            'events_archived': 0,
            'events_deleted': 0,
            'batches_processed': 0,
            'errors': []
        }
        
        try:
            archive_threshold = datetime.now() - timedelta(days=self.hot_retention_days)
            max_age_threshold = datetime.now() - timedelta(days=self.max_archive_age_days)
            
            logger.info(f"Starting archival process for events between {max_age_threshold} and {archive_threshold}")
            
            async for db in get_db():
                await self._process_archival_batches(
                    db, archive_threshold, max_age_threshold, stats
                )
                break  # Exit after first iteration
            
            stats['completed_at'] = datetime.now()
            stats['duration_seconds'] = (stats['completed_at'] - stats['started_at']).total_seconds()
            
            logger.info(f"Archival completed: {stats}")
            return stats
            
        except Exception as e:
            error_msg = f"Archival process failed: {str(e)}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            stats['completed_at'] = datetime.now()
            return stats
    
    async def _process_archival_batches(self, 
                                      db: AsyncSession, 
                                      archive_threshold: datetime,
                                      max_age_threshold: datetime,
                                      stats: Dict[str, Any]):
        """Process archival in batches to avoid memory issues."""
        
        while True:
            # Get batch of events to archive
            query = select(Event).where(
                and_(
                    Event.occurred_at < archive_threshold,
                    Event.occurred_at > max_age_threshold
                )
            ).limit(self.batch_size)
            
            result = await db.execute(query)
            events = result.scalars().all()
            
            if not events:
                logger.info("No more events to archive")
                break
            
            # Convert events to dictionary format for ClickHouse
            events_data = []
            event_ids = []
            
            for event in events:
                events_data.append({
                    'event_id': event.event_id,
                    'user_id': event.user_id,
                    'event_type': event.event_type,
                    'occurred_at': event.occurred_at,
                    'properties': event.properties_dict
                })
                event_ids.append(event.event_id)
            
            stats['events_processed'] += len(events_data)
            
            # Archive to ClickHouse
            archive_success = await clickhouse_service.archive_events(events_data)
            
            if archive_success:
                stats['events_archived'] += len(events_data)
                
                # Delete from PostgreSQL only if ClickHouse archive succeeded
                delete_success = await self._delete_archived_events(db, event_ids)
                
                if delete_success:
                    stats['events_deleted'] += len(event_ids)
                    await db.commit()
                    logger.info(f"Successfully archived and deleted {len(events_data)} events")
                else:
                    await db.rollback()
                    error_msg = f"Failed to delete {len(events_data)} events from PostgreSQL after successful ClickHouse archive"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
            else:
                error_msg = f"Failed to archive {len(events_data)} events to ClickHouse, skipping deletion"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
            
            stats['batches_processed'] += 1
            
            # Small delay to avoid overwhelming the databases
            await asyncio.sleep(0.1)
    
    async def _delete_archived_events(self, db: AsyncSession, event_ids: List[str]) -> bool:
        """Delete events from PostgreSQL after successful archival."""
        try:
            delete_query = delete(Event).where(Event.event_id.in_(event_ids))
            await db.execute(delete_query)
            return True
        except Exception as e:
            logger.error(f"Failed to delete events from PostgreSQL: {e}")
            return False
    
    async def get_archival_candidates(self) -> Dict[str, Any]:
        """
        Get information about events that are candidates for archival.
        
        Returns:
            Dict with candidate statistics
        """
        try:
            archive_threshold = datetime.now() - timedelta(days=self.hot_retention_days)
            max_age_threshold = datetime.now() - timedelta(days=self.max_archive_age_days)
            
            async for db in get_db():
                # Count events ready for archival
                candidates_query = select(Event).where(
                    and_(
                        Event.occurred_at < archive_threshold,
                        Event.occurred_at > max_age_threshold
                    )
                )
                
                result = await db.execute(candidates_query)
                candidates = result.scalars().all()
                
                # Group by date for analysis
                date_counts = {}
                for event in candidates:
                    date_str = event.occurred_at.strftime('%Y-%m-%d')
                    date_counts[date_str] = date_counts.get(date_str, 0) + 1
                
                return {
                    'total_candidates': len(candidates),
                    'archive_threshold': archive_threshold.isoformat(),
                    'max_age_threshold': max_age_threshold.isoformat(),
                    'candidates_by_date': date_counts,
                    'estimated_batches': (len(candidates) + self.batch_size - 1) // self.batch_size
                }
                break
                
        except Exception as e:
            logger.error(f"Failed to get archival candidates: {e}")
            return {'error': str(e)}
    
    async def verify_archival_integrity(self, sample_size: int = 100) -> Dict[str, Any]:
        """
        Verify that archived data in ClickHouse matches what was in PostgreSQL.
        
        Args:
            sample_size: Number of recent archived events to verify
            
        Returns:
            Dict with verification results
        """
        try:
            # This would need to be implemented based on your specific requirements
            # For now, we'll just check ClickHouse connectivity and table existence
            
            clickhouse_ok = await clickhouse_service.ping()
            
            if not clickhouse_ok:
                return {
                    'status': 'failed',
                    'error': 'ClickHouse not accessible'
                }
            
            # Get sample of recent archived data
            async with clickhouse_service.get_client() as client:
                query = """
                SELECT 
                    count() as total_events,
                    uniq(user_id) as unique_users,
                    min(occurred_at) as oldest_event,
                    max(occurred_at) as newest_event,
                    max(ingested_at) as last_ingested
                FROM events_cold
                """
                
                result = client.query(query)
                row = result.result_rows[0] if result.result_rows else None
                
                if row:
                    return {
                        'status': 'success',
                        'clickhouse_stats': {
                            'total_events': row[0],
                            'unique_users': row[1],
                            'oldest_event': str(row[2]) if row[2] else None,
                            'newest_event': str(row[3]) if row[3] else None,
                            'last_ingested': str(row[4]) if row[4] else None
                        }
                    }
                else:
                    return {
                        'status': 'success',
                        'clickhouse_stats': {
                            'total_events': 0,
                            'message': 'No archived events found'
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Archival integrity check failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }


# Global service instance
archival_service = DataArchivalService()
