"""
Statistics API endpoints for analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.logging import get_logger
from ...database.connection import get_db
from ...services.analytics_service import AnalyticsService
from ...core.deps import get_current_admin_user
from ...models.database import User

logger = get_logger(__name__)

router = APIRouter(tags=["statistics"])


@router.get(
    "/stats",
    summary="Basic Statistics",
    description="Get basic event statistics (Admin only)"
)
async def get_basic_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get basic event statistics.
    
    Returns:
    - Total events count
    - Unique users count  
    - Event types count
    """
    try:
        analytics_service = AnalyticsService(db)
        stats = await analytics_service.get_basic_stats()
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get basic stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate statistics"
        )


@router.get(
    "/stats/top-events",
    summary="Top Events",
    description="Get top event types by count (Admin only)"
)
async def get_top_events(
    from_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    limit: int = Query(10, ge=1, le=100, description="Number of top events to return"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get top event types by occurrence count.
    
    - **from_date**: Start date for filtering (YYYY-MM-DD)
    - **to_date**: End date for filtering (YYYY-MM-DD)  
    - **limit**: Number of top events to return (1-100)
    - Returns event types ordered by count (descending)
    """
    try:
        from datetime import datetime
        
        # Parse dates
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        
        # Validate date range
        if from_dt > to_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="from_date must be less than or equal to to_date"
            )
        
        analytics_service = AnalyticsService(db)
        top_events = await analytics_service.get_top_events(from_dt, to_dt, limit)
        
        return {
            "from_date": from_date,
            "to_date": to_date,
            "limit": limit,
            "data": top_events
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get top events", limit=limit, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate top events statistics"
        )


@router.get(
    "/stats/dau",
    summary="Daily Active Users",
    description="Get Daily Active Users statistics (Admin only)"
)
async def get_dau_stats(
    from_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get Daily Active Users statistics.
    
    - **from_date**: Start date for filtering (YYYY-MM-DD)
    - **to_date**: End date for filtering (YYYY-MM-DD)
    - Returns daily unique user counts
    """
    try:
        from datetime import datetime
        
        # Parse dates
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        
        # Validate date range
        if from_dt > to_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="from_date must be less than or equal to to_date"
            )
        
        analytics_service = AnalyticsService(db)
        dau_stats = await analytics_service.get_dau_stats(from_dt, to_dt)
        
        return {
            "from_date": from_date,
            "to_date": to_date,
            "data": dau_stats
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get DAU stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate DAU statistics"
        )


@router.get(
    "/stats/retention",
    summary="User Retention",  
    description="Get user retention statistics (Admin only)"
)
async def get_retention_stats(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    windows: int = Query(..., ge=1, le=10, description="Number of retention windows"),
    period_type: str = Query(..., description="Period type (daily, weekly, monthly)"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get user retention statistics.
    
    - **start_date**: Start date for cohort analysis (YYYY-MM-DD)
    - **windows**: Number of retention windows to analyze
    - **period_type**: Type of period (daily, weekly, monthly)
    """
    try:
        from datetime import datetime
        
        # Parse date
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        
        analytics_service = AnalyticsService(db)
        retention_stats = await analytics_service.get_retention_stats(start_dt, windows, period_type)
        
        return {
            "start_date": start_date,
            "windows": windows,
            "period_type": period_type,
            "data": retention_stats
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get retention stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate retention statistics"
        )


@router.get(
    "/stats/health",
    summary="Health check",
    description="Simple health check endpoint"
)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "statistics"}
