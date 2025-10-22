#!/usr/bin/env python3

import asyncio
import sys
import os
from datetime import datetime
from uuid import uuid4

# Додамо поточну папку до sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import AsyncSessionLocal
from app.services.event_service import EventService
from app.models.schemas import EventInput

async def test_create_event():
    """Тестуємо створення події через EventService."""
    try:
        async with AsyncSessionLocal() as session:
            service = EventService(session)
            
            # Створимо тестову подію
            test_event = EventInput(
                event_id=str(uuid4()),
                user_id=125,
                event_type="test_api",
                occurred_at=datetime.now(),
                properties={"test": True, "source": "test_script"}
            )
            
            print(f"Створюємо подію: {test_event.event_id}")
            
            responses, created, duplicates = await service.create_events([test_event])
            
            print(f"✅ Подія створена! Created: {created}, Duplicates: {duplicates}")
            for response in responses:
                print(f"  - {response.event_id}: {response.status}")
                
            return True
            
    except Exception as e:
        print(f"❌ Помилка створення події: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_create_event())
    sys.exit(0 if result else 1)
