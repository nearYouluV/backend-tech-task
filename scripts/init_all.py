#!/usr/bin/env python3
"""
Complete initialization script for Event Analytics API.
Creates database tables and admin user in one go.
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.connection import init_db
from app.core.config import settings
from app.core.auth import create_user, get_user_by_username
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


async def init_database():
    """Initialize database tables."""
    try:
        print("Creating database tables...")
        await init_db()
        print("Database tables created successfully!")
        return True
    except Exception as e:
        print(f"Error creating database tables: {e}")
        return False


async def create_admin_user():
    """Create default admin user."""
    try:
        print("Creating admin user...")
        
        # Create database engine and session
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            # Default admin credentials
            username = "admin"
            email = "admin@example.com"
            password = "admin1"
            
            # Check if admin user already exists
            existing_user = await get_user_by_username(db, username)
            if existing_user:
                print(f"Admin user '{username}' already exists")
                return True
                
            # Create admin user
            user = await create_user(
                db=db,
                username=username,
                email=email,
                password=password,
                is_admin=True
            )
            
            print(f"Admin user created successfully!")
            print(f"  Username: {username}")
            print(f"  Password: {password}")
            print(f"  Email: {email}")
            print("  SECURITY NOTE: Change the default password in production!")
            
        await engine.dispose()
        return True
            
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return False


async def main():
    """Initialize everything."""
    print("Starting complete initialization...")
    print("=" * 50)
    
    # Initialize database
    if not await init_database():
        print("Failed to initialize database")
        sys.exit(1)
    
    # Create admin user
    if not await create_admin_user():
        print("Failed to create admin user")
        sys.exit(1)
    
    print("=" * 50)
    print("Initialization completed successfully!")
    print("API is ready to use!")


if __name__ == "__main__":
    asyncio.run(main())
