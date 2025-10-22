#!/usr/bin/env python3

import asyncio
import sys
import os
from datetime import datetime
from uuid import uuid4

# Додамо поточну папку до sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.schemas import EventInput, EventsRequest

def test_pydantic_models():
    """Тестуємо Pydantic моделі."""
    try:
        # Тестуємо EventInput
        test_event = EventInput(
            event_id="550e8400-e29b-41d4-a716-446655440013",
            user_id=129,
            event_type="test_validation",
            occurred_at="2025-10-22T10:35:00+00:00",
            properties={"test": True}
        )
        
        print(f"✅ EventInput створено: {test_event.event_id}")
        print(f"Properties type: {type(test_event.properties)}")
        print(f"Properties: {test_event.properties}")
        
        # Тестуємо EventsRequest
        request = EventsRequest(events=[test_event])
        print(f"✅ EventsRequest створено з {len(request.events)} подій")
        
        # Серіалізуємо в JSON
        json_data = request.model_dump_json()
        print(f"✅ JSON серіалізація: {len(json_data)} символів")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка в Pydantic моделях: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_pydantic_models()
    sys.exit(0 if result else 1)
