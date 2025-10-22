"""
Tests for authentication functionality.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.auth import create_user, get_password_hash
from app.models.database import User


class TestAuthentication:
    """Test authentication endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from tests.conftest import override_get_db
        from app.database.connection import get_db
        
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def admin_user(self, db_session):
        """Create an admin user for testing."""
        user = User(
            id="test-admin-id",
            username="testadmin",
            email="admin@test.com",
            hashed_password=get_password_hash("testpass123"),
            is_admin=True,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    def test_login_success(self, client, admin_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testadmin",
                "password": "testpass123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["username"] == "testadmin"
        assert data["user"]["is_admin"] is True
    
    def test_login_invalid_credentials(self, client, admin_user):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testadmin",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password"
            }
        )
        
        assert response.status_code == 401
    
    def test_get_current_user_success(self, client, admin_user):
        """Test getting current user info with valid token."""
        # First login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testadmin",
                "password": "testpass123"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Then get user info
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == "testadmin"
        assert data["email"] == "admin@test.com"
        assert data["is_admin"] is True
        assert data["is_active"] is True
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user info without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 403  # No token provided
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user info with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
    
    def test_register_user_success(self, client, admin_user):
        """Test registering a new user (admin only)."""
        # First login as admin to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testadmin",
                "password": "testpass123"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Then register new user
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "newpass123",
                "is_admin": False
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@test.com"
        assert data["is_admin"] is False
        assert data["is_active"] is True
    
    def test_register_user_duplicate_username(self, client, admin_user):
        """Test registering user with duplicate username."""
        # Login as admin
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testadmin",
                "password": "testpass123"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Try to register with existing username
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testadmin",  # Already exists
                "email": "another@test.com",
                "password": "password123"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    def test_register_user_non_admin(self, client):
        """Test that non-admin users cannot register new users."""
        # Create a regular (non-admin) user and login
        from tests.conftest import sync_test_engine, SyncTestingSessionLocal
        from app.models.database import Base
        
        Base.metadata.create_all(bind=sync_test_engine)
        session = SyncTestingSessionLocal()
        
        regular_user = User(
            id="regular-user-id",
            username="regularuser",
            email="regular@test.com",
            hashed_password=get_password_hash("userpass123"),
            is_admin=False,
            is_active=True
        )
        session.add(regular_user)
        session.commit()
        session.close()
        
        # Login as regular user
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "regularuser",
                "password": "userpass123"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Try to register new user (should fail)
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser2",
                "email": "newuser2@test.com",
                "password": "password123"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    def test_auth_health_endpoint(self, client):
        """Test auth health endpoint."""
        response = client.get("/api/v1/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"
        assert "jwt_algorithm" in data
        assert "token_expire_minutes" in data
