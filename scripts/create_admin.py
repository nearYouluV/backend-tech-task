#!/usr/bin/env python3
"""
Create admin user script for Event Analytics API.
"""

import os
import sys
import asyncio
from getpass import getpass

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.auth import create_user, get_user_by_username
from app.models.database import Base


async def create_admin_user():
    """Create an admin user interactively."""
    print("🔐 Create Admin User for Event Analytics API")
    print("=" * 50)
    
    # Create database engine and session
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        # Get admin details
        print("\nEnter admin user details:")
        username = input("Username: ").strip()
        
        if not username:
            print("❌ Username cannot be empty")
            return
            
        # Check if user already exists
        existing_user = await get_user_by_username(db, username)
        if existing_user:
            print(f"❌ User '{username}' already exists")
            return
            
        email = input("Email: ").strip()
        if not email:
            print("❌ Email cannot be empty")
            return
            
        password = getpass("Password: ").strip()
        if not password:
            print("❌ Password cannot be empty")
            return
            
        password_confirm = getpass("Confirm password: ").strip()
        if password != password_confirm:
            print("❌ Passwords don't match")
            return
            
        if len(password) < 8:
            print("❌ Password must be at least 8 characters long")
            return
        
        # Create admin user
        try:
            user = await create_user(
                db=db,
                username=username,
                email=email,
                password=password,
                is_admin=True
            )
            
            print(f"\n✅ Admin user '{username}' created successfully!")
            print(f"User ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Created at: {user.created_at}")
            print("\nYou can now use this account to:")
            print("- Login to get JWT tokens")
            print("- Create other users")
            print("- Access protected API endpoints")
            
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            
    await engine.dispose()


async def main():
    """Main function."""
    try:
        await create_admin_user()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
