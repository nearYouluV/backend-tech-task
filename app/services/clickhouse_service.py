"""
ClickHouse service for cold storage analytics.
Handles data archival from hot PostgreSQL storage to cold ClickHouse storage.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from ..core.config import settings

logger = logging.getLogger(__name__)


class ClickHouseService:
    """Service for managing ClickHouse cold storage operations."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._connection_params = {
            'host': settings.CLICKHOUSE_HOST,
            'port': settings.CLICKHOUSE_PORT,
            'database': settings.CLICKHOUSE_DB,
            'username': settings.CLICKHOUSE_USER,
        }
        
        # Add password only if provided
        if settings.CLICKHOUSE_PASSWORD:
            self._connection_params['password'] = settings.CLICKHOUSE_PASSWORD
    
    @asynccontextmanager
    async def get_client(self):
        """Get ClickHouse client with connection management."""
        try:
            if not self.client:
                self.client = clickhouse_connect.get_client(**self._connection_params)
            yield self.client
        except Exception as e:
            logger.error(f"ClickHouse connection error: {e}")
            raise
    
    async def ping(self) -> bool:
        """Check ClickHouse connectivity."""
        try:
            async with self.get_client() as client:
                result = client.ping()
                return result
        except Exception as e:
            logger.error(f"ClickHouse ping failed: {e}")
            return False
    
    async def archive_events(self, events_data: List[Dict[str, Any]]) -> bool:
        """
        Archive events to ClickHouse cold storage.
        
        Args:
            events_data: List of event dictionaries from PostgreSQL
            
        Returns:
            bool: Success status
        """
        if not events_data:
            logger.info("No events to archive")
            return True
            
        try:
            async with self.get_client() as client:
                # Prepare data for ClickHouse insertion
                formatted_data = []
                for event in events_data:
                    # Convert properties to JSON string if it's a dict
                    properties_json = event.get('properties', '{}')
                    if isinstance(properties_json, dict):
                        import json
                        properties_json = json.dumps(properties_json)
                    
                    formatted_data.append([
                        str(event['event_id']),  # UUID as string
                        event['user_id'],
                        event['event_type'],
                        event['occurred_at'],
                        properties_json,
                        datetime.now()  # ingested_at
                    ])
                
                # Insert data into ClickHouse
                client.insert(
                    'events_cold',
                    formatted_data,
                    column_names=[
                        'event_id', 'user_id', 'event_type', 
                        'occurred_at', 'properties', 'ingested_at'
                    ]
                )
                
                logger.info(f"Successfully archived {len(events_data)} events to ClickHouse")
                return True
                
        except Exception as e:
            logger.error(f"Failed to archive events to ClickHouse: {e}")
            return False
    
    async def get_dau_fast(self, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Get Daily Active Users using ClickHouse materialized view (super fast).
        
        Args:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            
        Returns:
            List of DAU data per day
        """
        try:
            async with self.get_client() as client:
                query = """
                SELECT 
                    event_date,
                    uniq(user_id) as daily_active_users
                FROM mv_daily_active_users 
                WHERE event_date >= toDate(%(from_date)s) 
                  AND event_date <= toDate(%(to_date)s)
                GROUP BY event_date
                ORDER BY event_date
                """
                
                result = client.query(
                    query, 
                    parameters={'from_date': from_date, 'to_date': to_date}
                )
                
                return [
                    {
                        'date': str(row[0]),
                        'daily_active_users': row[1]
                    }
                    for row in result.result_rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to get DAU from ClickHouse: {e}")
            return []
    
    async def get_top_events_fast(self, from_date: str, to_date: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top event types using ClickHouse materialized view.
        
        Args:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            limit: Maximum number of results
            
        Returns:
            List of top event types with counts
        """
        try:
            async with self.get_client() as client:
                query = """
                SELECT 
                    event_type,
                    sum(event_count) as total_count
                FROM mv_event_type_stats 
                WHERE event_date >= toDate(%(from_date)s) 
                  AND event_date <= toDate(%(to_date)s)
                GROUP BY event_type
                ORDER BY total_count DESC
                LIMIT %(limit)s
                """
                
                result = client.query(
                    query, 
                    parameters={
                        'from_date': from_date, 
                        'to_date': to_date,
                        'limit': limit
                    }
                )
                
                return [
                    {
                        'event_type': row[0],
                        'count': row[1]
                    }
                    for row in result.result_rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to get top events from ClickHouse: {e}")
            return []
    
    async def get_retention_cohort(self, start_date: str, windows: int = 4) -> List[Dict[str, Any]]:
        """
        Calculate retention cohorts using ClickHouse (weekly cohorts).
        
        Args:
            start_date: Cohort start date (YYYY-MM-DD)
            windows: Number of weeks to analyze
            
        Returns:
            List of cohort retention data
        """
        try:
            async with self.get_client() as client:
                query = """
                WITH cohort_users AS (
                    SELECT DISTINCT user_id
                    FROM events_cold
                    WHERE toDate(occurred_at) >= toDate(%(start_date)s)
                      AND toDate(occurred_at) < toDate(%(start_date)s) + INTERVAL 7 DAY
                )
                SELECT 
                    week_number,
                    uniq(user_id) as retained_users,
                    (uniq(user_id) * 100.0) / (SELECT count() FROM cohort_users) as retention_rate
                FROM (
                    SELECT 
                        user_id,
                        intDiv(toDayOfYear(occurred_at) - toDayOfYear(toDate(%(start_date)s)), 7) as week_number
                    FROM events_cold
                    WHERE user_id IN (SELECT user_id FROM cohort_users)
                      AND toDate(occurred_at) >= toDate(%(start_date)s)
                      AND toDate(occurred_at) < toDate(%(start_date)s) + INTERVAL %(windows)s WEEK
                    GROUP BY user_id, week_number
                )
                GROUP BY week_number
                ORDER BY week_number
                """
                
                result = client.query(
                    query,
                    parameters={
                        'start_date': start_date,
                        'windows': windows
                    }
                )
                
                return [
                    {
                        'week': row[0],
                        'retained_users': row[1],
                        'retention_rate': round(row[2], 2)
                    }
                    for row in result.result_rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to calculate retention cohorts: {e}")
            return []
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get ClickHouse storage statistics."""
        try:
            async with self.get_client() as client:
                # Get table sizes
                size_query = """
                SELECT 
                    table,
                    formatReadableSize(sum(bytes_on_disk)) as size_on_disk,
                    sum(rows) as total_rows
                FROM system.parts 
                WHERE database = %(database)s
                  AND active = 1
                GROUP BY table
                ORDER BY sum(bytes_on_disk) DESC
                """
                
                size_result = client.query(
                    size_query,
                    parameters={'database': settings.CLICKHOUSE_DB}
                )
                
                # Get partition info
                partition_query = """
                SELECT 
                    table,
                    partition,
                    count() as parts_count,
                    sum(rows) as rows_count
                FROM system.parts 
                WHERE database = %(database)s
                  AND active = 1
                GROUP BY table, partition
                ORDER BY table, partition
                LIMIT 20
                """
                
                partition_result = client.query(
                    partition_query,
                    parameters={'database': settings.CLICKHOUSE_DB}
                )
                
                return {
                    'table_sizes': [
                        {
                            'table': row[0],
                            'size_on_disk': row[1],
                            'total_rows': row[2]
                        }
                        for row in size_result.result_rows
                    ],
                    'partitions': [
                        {
                            'table': row[0],
                            'partition': row[1],
                            'parts_count': row[2],
                            'rows_count': row[3]
                        }
                        for row in partition_result.result_rows
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}


# Global service instance
clickhouse_service = ClickHouseService()
