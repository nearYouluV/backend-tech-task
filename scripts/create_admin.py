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


#!/usr/bin/env python3
"""
Create default admin user script for Event Analytics API.
Automatically creates admin user with username: admin, password: admin1
"""

import os
import sys
import asyncio

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.auth import create_user, get_user_by_username
from app.models.database import Base


async def create_default_admin():
    """Create default admin user with predefined credentials."""
    print("🔐 Creating Default Admin User")
    print("=" * 40)
    
    # Create database engine and session
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        # Default admin credentials
        username = "admin"
        email = "admin@example.com"
        password = "admin1"
        
        # Check if admin user already exists
        existing_user = await get_user_by_username(db, username)
        if existing_user:
            print(f"❌ Admin user '{username}' already exists!")
            print(f"   Email: {existing_user.email}")
            print(f"   Is Admin: {existing_user.is_admin}")
            print(f"   Created: {existing_user.created_at}")
            return True
            
        # Create admin user
        try:
            user = await create_user(
                db=db,
                username=username,
                email=email,
                password=password,
                is_admin=True
            )
            
            print(f"✅ Default admin user created successfully!")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
            print(f"   Email: {email}")
            print(f"   User ID: {user.id}")
            print(f"   Created: {user.created_at}")
            print()
            print("🔐 Login credentials:")
            print('   POST /api/v1/auth/login')
            print('   {"username": "admin", "password": "admin1"}')
            print()
            print("⚠️  SECURITY NOTE: Change the default password in production!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            return False
            
    await engine.dispose()


async def main():
    """Main function."""
    try:
        success = await create_default_admin()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
