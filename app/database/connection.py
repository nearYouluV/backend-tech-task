"""
Async database connection configuration for events API.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from typing import AsyncGenerator

from ..core.config import settings
from ..models.database import Base


def get_database_url(async_url: bool = False) -> str:
    """Get database URL, optionally for async connection."""
    url = settings.DATABASE_URL
    
    if async_url:
        # Convert to async URL if needed
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://")
    
    return url


# Create async engine
async_engine = create_async_engine(
    get_database_url(async_url=True),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Initialize database and create tables."""
    # Create sync engine for table creation
    sync_engine = create_engine(get_database_url(async_url=False))
    
    # Create tables synchronously
    Base.metadata.create_all(bind=sync_engine)
    
    sync_engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database dependency for FastAPI routes.
    
    Yields:
        AsyncSession: SQLAlchemy async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
