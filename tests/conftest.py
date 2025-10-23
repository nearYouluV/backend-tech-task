"""
Test configuration and fixtures.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv

from app.database.connection import get_db
from app.main import app
from app.models.database import Base

# Load test environment variables
load_dotenv(".env.test")

# Get database configuration from environment
POSTGRES_USER = os.getenv("POSTGRES_USER", "events_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "events_password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5433")  # Default to test port
POSTGRES_DB = os.getenv("POSTGRES_DB", "events")

# Test database URLs - using PostgreSQL from environment variables
SYNC_TEST_DB_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
ASYNC_TEST_DB_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Sync engine for simple testing
sync_test_engine = create_engine(SYNC_TEST_DB_URL)
SyncTestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_test_engine)

# Async engine for API dependency override
async_test_engine = create_async_engine(ASYNC_TEST_DB_URL)
AsyncTestingSessionLocal = async_sessionmaker(
    async_test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    """Override database dependency for testing."""
    session = AsyncTestingSessionLocal()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a synchronous database session for service tests."""
    # Create tables
    Base.metadata.create_all(bind=sync_test_engine)
    
    session = SyncTestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
    
    # Drop tables
    Base.metadata.drop_all(bind=sync_test_engine)


@pytest.fixture(scope="function")
def client():
    """Create test client with database override."""
    # Create tables for async API
    Base.metadata.create_all(bind=sync_test_engine)
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
    
    # Drop tables
    Base.metadata.drop_all(bind=sync_test_engine)


# Add cleanup fixture for async engine
@pytest.fixture(scope="session", autouse=True)
def cleanup_engines():
    """Ensure engines are properly disposed of after tests."""
    yield
    # Clean up engines at the end of test session
    import asyncio
    
    # Clean up sync engine
    sync_test_engine.dispose()
    
    # Clean up async engine
    try:
        # Check if there's a current event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, schedule cleanup
            loop.create_task(async_test_engine.dispose())
        except RuntimeError:
            # No running loop, create one for cleanup
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(async_test_engine.dispose())
            finally:
                loop.close()
    except Exception:
        # Fallback - force close any remaining connections
        pass
