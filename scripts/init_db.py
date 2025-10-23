#!/usr/bin/env python3
"""
Database initialization script.
Creates tables if they don't exist.
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.connection import init_db


async def main():
    """Initialize database tables."""
    try:
        print("Creating database tables...")
        await init_db()
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
