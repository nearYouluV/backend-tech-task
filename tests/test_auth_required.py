"""
Test authentication failures for protected endpoints.
"""

import pytest
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app


class TestAuthenticationRequired:
    """Test that protected endpoints require authentication."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from tests.conftest import override_get_db
        from app.database.connection import get_db
        
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()
    
    def test_post_events_without_auth(self, client):
        """Test that POST /events requires authentication."""
        event_data = {
            "events": [{
                "event_id": str(uuid4()),
                "occurred_at": datetime.now().isoformat(),
                "user_id": 1,
                "event_type": "test_event",
                "properties": {"test": True}
            }]
        }
        
        response = client.post("/api/v1/events", json=event_data)
        assert response.status_code == 403  # Forbidden without auth
    
    def test_post_events_with_invalid_token(self, client):
        """Test that POST /events rejects invalid tokens."""
        event_data = {
            "events": [{
                "event_id": str(uuid4()),
                "occurred_at": datetime.now().isoformat(),
                "user_id": 1,
                "event_type": "test_event",
                "properties": {"test": True}
            }]
        }
        
        response = client.post(
            "/api/v1/events", 
            json=event_data,
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401  # Unauthorized with invalid token
