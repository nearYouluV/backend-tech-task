#!/usr/bin/env python3

import sys
import os
from datetime import datetime

# Додамо поточну папку до sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from app.models.schemas import EventsRequest, EventsResponse
import uvicorn

app = FastAPI(title="Debug API")

@app.post("/debug/events")
async def debug_events(events_request: EventsRequest):
    """Debug endpoint для тестування POST запитів."""
    try:
        print(f"Отримано {len(events_request.events)} подій")
        
        for i, event in enumerate(events_request.events):
            print(f"Подія {i+1}:")
            print(f"  event_id: {event.event_id} ({type(event.event_id)})")
            print(f"  user_id: {event.user_id} ({type(event.user_id)})")
            print(f"  event_type: {event.event_type} ({type(event.event_type)})")
            print(f"  occurred_at: {event.occurred_at} ({type(event.occurred_at)})")
            print(f"  properties: {event.properties} ({type(event.properties)})")
        
        return {
            "status": "success",
            "received_events": len(events_request.events),
            "first_event_id": str(events_request.events[0].event_id) if events_request.events else None
        }
        
    except Exception as e:
        print(f"Помилка: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.get("/debug/health")
async def health():
    return {"status": "ok", "message": "Debug server running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
