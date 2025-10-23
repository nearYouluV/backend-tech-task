"""
Cold storage analytics API endpoints.
Provides fast analytics queries using ClickHouse cold storage.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any

from ...core.deps import get_current_admin_user
from ...models.database import User
from ...services.clickhouse_service import clickhouse_service
from ...services.archival_service import archival_service

router = APIRouter()


@router.get("/health")
async def clickhouse_health():
    """Check ClickHouse cold storage health."""
    try:
        is_healthy = await clickhouse_service.ping()
        stats = await clickhouse_service.get_storage_stats()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "clickhouse_accessible": is_healthy,
            "storage_stats": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/dau-fast")
async def get_dau_from_cold_storage(
    from_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get Daily Active Users from ClickHouse cold storage (super fast).
    
    This endpoint uses ClickHouse materialized views for lightning-fast queries
    on large datasets. Perfect for dashboards and real-time analytics.
    """
    try:
        # Validate date format
        datetime.strptime(from_date, '%Y-%m-%d')
        datetime.strptime(to_date, '%Y-%m-%d')
        
        dau_data = await clickhouse_service.get_dau_fast(from_date, to_date)
        
        return {
            "from_date": from_date,
            "to_date": to_date,
            "daily_active_users": dau_data,
            "total_days": len(dau_data),
            "data_source": "clickhouse_cold_storage"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get DAU from cold storage: {e}")


@router.get("/top-events-fast")
async def get_top_events_from_cold_storage(
    from_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    limit: int = Query(default=10, description="Maximum number of results"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get top event types from ClickHouse cold storage.
    
    Uses pre-aggregated materialized views for instant results.
    """
    try:
        # Validate date format
        datetime.strptime(from_date, '%Y-%m-%d')
        datetime.strptime(to_date, '%Y-%m-%d')
        
        if limit <= 0 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        top_events = await clickhouse_service.get_top_events_fast(from_date, to_date, limit)
        
        return {
            "from_date": from_date,
            "to_date": to_date,
            "limit": limit,
            "top_events": top_events,
            "data_source": "clickhouse_cold_storage"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get top events from cold storage: {e}")


@router.get("/retention-cohort")
async def get_retention_from_cold_storage(
    start_date: str = Query(..., description="Cohort start date (YYYY-MM-DD)"),
    windows: int = Query(default=4, description="Number of weeks to analyze"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Calculate retention cohorts using ClickHouse analytics.
    
    Analyzes user retention over weekly periods using powerful ClickHouse aggregations.
    """
    try:
        # Validate date format
        datetime.strptime(start_date, '%Y-%m-%d')
        
        if windows <= 0 or windows > 52:
            raise HTTPException(status_code=400, detail="Windows must be between 1 and 52 weeks")
        
        retention_data = await clickhouse_service.get_retention_cohort(start_date, windows)
        
        return {
            "cohort_start_date": start_date,
            "analysis_windows": windows,
            "retention_cohorts": retention_data,
            "data_source": "clickhouse_cold_storage"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate retention cohorts: {e}")


@router.post("/archive-now")
async def trigger_manual_archival(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Manually trigger data archival from hot to cold storage.
    
    This endpoint allows administrators to trigger immediate archival of old events
    from PostgreSQL to ClickHouse. The process runs in the background.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can trigger manual archival")
    
    try:
        # Get archival candidates first
        candidates = await archival_service.get_archival_candidates()
        
        if candidates.get('total_candidates', 0) == 0:
            return {
                "message": "No events ready for archival",
                "candidates": candidates
            }
        
        # Add archival task to background
        background_tasks.add_task(archival_service.archive_old_events)
        
        return {
            "message": "Archival process started in background",
            "candidates_info": candidates,
            "note": "Check /cold-storage/archival-status for progress"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger archival: {e}")


@router.get("/archival-candidates")
async def get_archival_candidates(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get information about events ready for archival.
    
    Shows how many events are candidates for moving from hot to cold storage.
    """
    try:
        candidates = await archival_service.get_archival_candidates()
        return candidates
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get archival candidates: {e}")


@router.get("/archival-integrity")
async def verify_archival_integrity(
    sample_size: int = Query(default=100, description="Sample size for verification"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Verify integrity of archived data in cold storage.
    
    Performs basic checks to ensure archived data is properly stored in ClickHouse.
    """
    try:
        if sample_size <= 0 or sample_size > 1000:
            raise HTTPException(status_code=400, detail="Sample size must be between 1 and 1000")
        
        integrity_check = await archival_service.verify_archival_integrity(sample_size)
        return integrity_check
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify archival integrity: {e}")


@router.get("/storage-comparison")
async def compare_hot_cold_storage(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Compare data distribution between hot (PostgreSQL) and cold (ClickHouse) storage.
    
    Provides insights into the data tiering strategy effectiveness.
    """
    try:
        # Get ClickHouse stats
        clickhouse_stats = await clickhouse_service.get_storage_stats()
        
        # Get PostgreSQL stats (you could extend this)
        from ...database.connection import get_db
        from sqlalchemy import select, func
        from ...models.database import Event
        
        async for db in get_db():
            # Count events in hot storage
            hot_count_query = select(func.count(Event.event_id))
            hot_result = await db.execute(hot_count_query)
            hot_count = hot_result.scalar()
            
            # Get date range in hot storage
            date_range_query = select(
                func.min(Event.occurred_at).label('oldest'),
                func.max(Event.occurred_at).label('newest')
            )
            date_result = await db.execute(date_range_query)
            date_row = date_result.first()
            
            hot_stats = {
                'total_events': hot_count,
                'oldest_event': str(date_row.oldest) if date_row.oldest else None,
                'newest_event': str(date_row.newest) if date_row.newest else None
            }
            break
        
        return {
            "hot_storage": {
                "storage_type": "postgresql",
                "stats": hot_stats
            },
            "cold_storage": {
                "storage_type": "clickhouse", 
                "stats": clickhouse_stats
            },
            "strategy": {
                "hot_retention_days": 7,
                "description": "Recent events in PostgreSQL for fast writes, older events in ClickHouse for fast analytics"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare storage: {e}")
