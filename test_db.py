#!/usr/bin/env python3

import asyncio
import sys
import os

# Додамо поточну папку до sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.database.connection import AsyncSessionLocal
from app.models.database import Event
from sqlalchemy import select

async def test_db_connection():
    """Тестуємо підключення до бази даних."""
    try:
        print(f"Підключаємося до: {settings.DATABASE_URL}")
        
        async with AsyncSessionLocal() as session:
            # Простий запит для перевірки підключення
            result = await session.execute(select(Event))
            events = result.scalars().all()
            
            print(f"✅ Підключення успішне! Знайдено {len(events)} подій.")
            for event in events:
                print(f"  - {event.event_id}: {event.event_type}")
                
            return True
            
    except Exception as e:
        print(f"❌ Помилка підключення: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_db_connection())
    sys.exit(0 if result else 1)
