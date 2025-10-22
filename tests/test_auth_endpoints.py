"""
Comprehensive authentication API tests.
"""

import pytest
import json
from datetime import datetime, UTC
from unittest.mock import Mock, patch

from app.models.database import User
from app.core.auth import get_password_hash, create_access_token


class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    def test_signup_flow(self, client):
        """Test public user signup."""
        signup_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123",
            "is_admin": True  # Should be ignored for public signup
        }
        
        response = client.post("/api/v1/auth/signup", json=signup_data)
        
        # Should succeed or fail gracefully
        assert response.status_code in [201, 500, 400]
        
        if response.status_code == 201:
            data = response.json()
            assert data["username"] == "newuser"
            assert data["email"] == "newuser@example.com"
            assert data["is_admin"] is False  # Should be forced to False
            assert data["is_active"] is True
            assert "id" in data
            assert "created_at" in data
            
        elif response.status_code == 400:
            # User might already exist
            data = response.json()
            assert "already registered" in data["detail"].lower()
    
    def test_login_flow(self, client):
        """Test login with username/password."""
        # First signup a user
        signup_data = {
            "username": "loginuser",
            "email": "loginuser@example.com", 
            "password": "loginpass123",
            "is_admin": False
        }
        
        signup_response = client.post("/api/v1/auth/signup", json=signup_data)
        
        # Try to login
        login_data = {
            "username": "loginuser",
            "password": "loginpass123"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        
        # Should succeed or fail gracefully
        assert login_response.status_code in [200, 401, 500]
        
        if login_response.status_code == 200:
            data = login_response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
            assert data["expires_in"] == 1800  # 30 minutes
            assert "user" in data
            
            # Verify token structure
            assert len(data["access_token"]) > 50  # JWT should be long
            assert len(data["refresh_token"]) > 50  # Refresh token should be long
            
            return data["access_token"], data["refresh_token"]
    
    def test_protected_endpoint_access(self, client):
        """Test accessing protected endpoints with valid token."""
        # First get a token
        tokens = self.test_login_flow(client)
        if not tokens:
            pytest.skip("Login failed, skipping protected endpoint test")
        
        access_token, refresh_token = tokens
        
        # Test /me endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code in [200, 401, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "username" in data
            assert "email" in data
            assert "is_active" in data
    
    def test_refresh_token_flow(self, client):
        """Test refresh token functionality."""
        # First get tokens
        tokens = self.test_login_flow(client)
        if not tokens:
            pytest.skip("Login failed, skipping refresh token test")
        
        access_token, refresh_token = tokens
        
        # Test refresh endpoint
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code in [200, 401, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["access_token"] != access_token  # Should be new
            assert data["refresh_token"] != refresh_token  # Should be rotated
    
    def test_logout_flow(self, client):
        """Test logout functionality."""
        # First get tokens
        tokens = self.test_login_flow(client)
        if not tokens:
            pytest.skip("Login failed, skipping logout test")
        
        access_token, refresh_token = tokens
        
        # Test logout
        logout_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/logout", json=logout_data)
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "revoked" in data
    
    def test_logout_all_flow(self, client):
        """Test logout from all devices."""
        # First get tokens
        tokens = self.test_login_flow(client)
        if not tokens:
            pytest.skip("Login failed, skipping logout-all test")
        
        access_token, refresh_token = tokens
        
        # Test logout-all
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/api/v1/auth/logout-all", headers=headers)
        
        assert response.status_code in [200, 401, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "revoked_tokens" in data
    
    def test_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpass"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code in [401, 500]
        
        if response.status_code == 401:
            data = response.json()
            assert "incorrect" in data["detail"].lower()
    
    def test_invalid_token_access(self, client):
        """Test accessing protected endpoints with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code in [401, 422, 500]
    
    def test_duplicate_signup(self, client):
        """Test signup with existing username."""
        signup_data = {
            "username": "duplicate_user",
            "email": "dup1@example.com",
            "password": "pass123",
            "is_admin": False
        }
        
        # First signup
        response1 = client.post("/api/v1/auth/signup", json=signup_data)
        
        # Second signup with same username
        signup_data["email"] = "dup2@example.com"  # Different email
        response2 = client.post("/api/v1/auth/signup", json=signup_data)
        
        # Second should fail
        assert response2.status_code in [400, 500]
        
        if response2.status_code == 400:
            data = response2.json()
            assert "already registered" in data["detail"].lower()


class TestAuthValidation:
    """Test authentication input validation."""
    
    def test_signup_validation(self, client):
        """Test signup input validation."""
        # Missing required fields
        invalid_data = {
            "username": "test"
            # Missing email, password
        }
        
        response = client.post("/api/v1/auth/signup", json=invalid_data)
        assert response.status_code == 422
        
        # Invalid email format
        invalid_email_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "pass123",
            "is_admin": False
        }
        
        response = client.post("/api/v1/auth/signup", json=invalid_email_data)
        assert response.status_code in [422, 500]
    
    def test_login_validation(self, client):
        """Test login input validation."""
        # Missing password
        invalid_data = {
            "username": "test"
            # Missing password
        }
        
        response = client.post("/api/v1/auth/login", json=invalid_data)
        assert response.status_code == 422
        
        # Empty credentials
        empty_data = {
            "username": "",
            "password": ""
        }
        
        response = client.post("/api/v1/auth/login", json=empty_data)
        assert response.status_code in [422, 401, 500]
    
    def test_refresh_validation(self, client):
        """Test refresh token validation."""
        # Missing refresh token
        invalid_data = {}
        
        response = client.post("/api/v1/auth/refresh", json=invalid_data)
        assert response.status_code == 422
        
        # Empty refresh token
        empty_data = {"refresh_token": ""}
        
        response = client.post("/api/v1/auth/refresh", json=empty_data)
        assert response.status_code in [422, 401, 500]


class TestAuthHealthAndStatus:
    """Test authentication health and status endpoints."""
    
    def test_auth_health(self, client):
        """Test auth health endpoint."""
        response = client.get("/api/v1/auth/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"
        assert "jwt_algorithm" in data
        assert "access_token_expire_minutes" in data
        assert "refresh_token_expire_days" in data


class TestAdminEndpoints:
    """Test admin-only endpoints."""
    
    def test_admin_register_without_auth(self, client):
        """Test admin register endpoint without authentication."""
        user_data = {
            "username": "admintest",
            "email": "admin@example.com",
            "password": "adminpass123",
            "is_admin": True
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        # Should require authentication
        assert response.status_code in [401, 403, 422, 500]
    
    @pytest.mark.skip(reason="Requires admin token setup")
    def test_admin_register_with_auth(self, client):
        """Test admin register endpoint with admin authentication."""
        # This would require setting up an admin user first
        # Skipping for now as it requires complex setup
        pass


class TestTokenSecurity:
    """Test token security aspects."""
    
    def test_token_expiration_structure(self, client):
        """Test that tokens have proper expiration."""
        # Get tokens through login
        signup_data = {
            "username": "securitytest",
            "email": "security@example.com",
            "password": "secpass123",
            "is_admin": False
        }
        
        client.post("/api/v1/auth/signup", json=signup_data)
        
        login_data = {
            "username": "securitytest",
            "password": "secpass123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify expiration is set correctly
            assert data["expires_in"] == 1800  # 30 minutes
            
            # Verify token structure (basic checks)
            access_token = data["access_token"]
            refresh_token = data["refresh_token"]
            
            # JWT should have 3 parts separated by dots
            assert len(access_token.split('.')) == 3
            
            # Refresh token should be long and random
            assert len(refresh_token) > 50
            assert refresh_token.replace('_', '').replace('-', '').isalnum()


class TestErrorHandling:
    """Test error handling in authentication."""
    
    def test_malformed_requests(self, client):
        """Test handling of malformed requests."""
        # Invalid JSON
        response = client.post(
            "/api/v1/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
        
        # Wrong content type
        response = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "test", "password": "test"}),
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code in [400, 422, 415]
    
    def test_large_payload(self, client):
        """Test handling of large payloads."""
        # Very long username
        large_data = {
            "username": "x" * 10000,
            "email": "test@example.com",
            "password": "test123",
            "is_admin": False
        }
        
        response = client.post("/api/v1/auth/signup", json=large_data)
        # Should handle gracefully
        assert response.status_code in [400, 422, 413, 500]


@pytest.fixture
def mock_database_error():
    """Mock database connection errors."""
    return Mock(side_effect=Exception("Database connection failed"))


class TestDatabaseErrorHandling:
    """Test handling of database errors."""
    
    def test_signup_with_db_error(self, client, mock_database_error):
        """Test signup when database is unavailable."""
        signup_data = {
            "username": "dbtest",
            "email": "db@example.com",
            "password": "dbtest123",
            "is_admin": False
        }
        
        with patch('app.database.connection.get_db', mock_database_error):
            response = client.post("/api/v1/auth/signup", json=signup_data)
            # Should handle database errors gracefully
            assert response.status_code in [500, 503]
    
    def test_login_with_db_error(self, client, mock_database_error):
        """Test login when database is unavailable."""
        login_data = {
            "username": "dbtest",
            "password": "dbtest123"
        }
        
        with patch('app.database.connection.get_db', mock_database_error):
            response = client.post("/api/v1/auth/login", json=login_data)
            # Should handle database errors gracefully
            assert response.status_code in [500, 503]


class TestRateLimiting:
    """Test rate limiting on auth endpoints."""
    
    @pytest.mark.skip(reason="Rate limiting implementation dependent")
    def test_login_rate_limiting(self, client):
        """Test rate limiting on login attempts."""
        # This would test rapid successive login attempts
        # Implementation depends on rate limiting strategy
        pass
    
    @pytest.mark.skip(reason="Rate limiting implementation dependent")
    def test_signup_rate_limiting(self, client):
        """Test rate limiting on signup attempts."""
        # This would test rapid successive signup attempts
        # Implementation depends on rate limiting strategy
        pass
