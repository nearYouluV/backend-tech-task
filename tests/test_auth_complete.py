"""
Complete JWT authentication tests.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from app.core.auth import (
    create_user, authenticate_user, get_user_by_username,
    verify_password, get_password_hash
)
from app.models.database import User


class TestUserAuthentication:
    """Test user authentication flow."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = Mock()
        return db
    
    def test_create_user(self, mock_db):
        """Test user creation."""
        async def test():
            user = await create_user(
                db=mock_db,
                username="newuser",
                email="new@example.com",
                password="password123",
                is_admin=False
            )
            
            assert user.username == "newuser"
            assert user.email == "new@example.com"
            assert user.is_admin is False
            assert user.is_active is True
            assert user.hashed_password != "password123"  # Should be hashed
            assert mock_db.add.called
            assert mock_db.commit.called
        
        asyncio.run(test())
    
    def test_authenticate_user_success(self, mock_db):
        """Test successful user authentication."""
        async def test():
            # Create test user with hashed password
            hashed_password = get_password_hash("correct_password")
            test_user = User(
                id="user-id",
                username="testuser",
                email="test@example.com",
                hashed_password=hashed_password,
                is_active=True,
                is_admin=False
            )
            
            # Mock database query
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = test_user
            mock_db.execute.return_value = mock_result
            
            user = await authenticate_user(mock_db, "testuser", "correct_password")
            
            assert user is not None
            assert user.username == "testuser"
            assert user.is_active is True
        
        asyncio.run(test())
    
    def test_authenticate_user_wrong_password(self, mock_db):
        """Test authentication with wrong password."""
        async def test():
            # Create test user with hashed password
            hashed_password = get_password_hash("correct_password")
            test_user = User(
                id="user-id",
                username="testuser",
                email="test@example.com",
                hashed_password=hashed_password,
                is_active=True,
                is_admin=False
            )
            
            # Mock database query
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = test_user
            mock_db.execute.return_value = mock_result
            
            user = await authenticate_user(mock_db, "testuser", "wrong_password")
            
            assert user is None  # Should return None for wrong password
        
        asyncio.run(test())
    
    def test_authenticate_user_not_found(self, mock_db):
        """Test authentication with non-existent user."""
        async def test():
            # Mock database query returning no user
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            
            user = await authenticate_user(mock_db, "nonexistent", "password")
            
            assert user is None
        
        asyncio.run(test())
    
    def test_authenticate_inactive_user(self, mock_db):
        """Test authentication with inactive user."""
        async def test():
            # Create inactive test user
            hashed_password = get_password_hash("correct_password")
            test_user = User(
                id="user-id",
                username="testuser",
                email="test@example.com",
                hashed_password=hashed_password,
                is_active=False,  # Inactive user
                is_admin=False
            )
            
            # Mock database query
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = test_user
            mock_db.execute.return_value = mock_result
            
            user = await authenticate_user(mock_db, "testuser", "correct_password")
            
            assert user is None  # Should return None for inactive user
        
        asyncio.run(test())
    
    def test_get_user_by_username(self, mock_db):
        """Test getting user by username."""
        async def test():
            test_user = User(
                id="user-id",
                username="testuser",
                email="test@example.com",
                hashed_password="hashed",
                is_active=True,
                is_admin=False
            )
            
            # Mock database query
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = test_user
            mock_db.execute.return_value = mock_result
            
            user = await get_user_by_username(mock_db, "testuser")
            
            assert user is not None
            assert user.username == "testuser"
        
        asyncio.run(test())


class TestPasswordSecurity:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password  # Should be different
        assert len(hashed) > 20  # Should be reasonably long
        assert hashed.startswith("$2b$")  # bcrypt format
    
    def test_password_verification_correct(self):
        """Test correct password verification."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_incorrect(self):
        """Test incorrect password verification."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes."""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # bcrypt includes salt, so hashes should be different
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestAuthenticationAPI:
    """Test authentication API endpoints."""
    
    def test_register_endpoint_admin_required(self, client):
        """Test that registration requires admin privileges."""
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
            "is_admin": False
        }
        
        # Without admin token
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden
    
    def test_login_endpoint_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent",
            "password": "wrong_password"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code in [401, 500]  # Should be unauthorized
    
    def test_me_endpoint_no_token(self, client):
        """Test /me endpoint without authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code in [401, 403]  # Should require authentication
    
    def test_health_endpoint(self, client):
        """Test authentication health endpoint."""
        response = client.get("/api/v1/auth/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"
        assert "jwt_algorithm" in data
        assert "access_token_expire_minutes" in data


class TestFullAuthenticationFlow:
    """Test complete authentication flow."""
    
    def test_complete_flow_simulation(self, client):
        """Simulate complete authentication flow."""
        # 1. Try to access protected endpoint without auth
        protected_response = client.get("/api/v1/auth/me")
        assert protected_response.status_code in [401, 403]
        
        # 2. Try to login with non-existent user
        login_response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "password"
        })
        assert login_response.status_code in [401, 500]
        
        # 3. Check health endpoints
        auth_health = client.get("/api/v1/auth/health")
        assert auth_health.status_code == 200
        
        # 4. Test refresh with invalid token
        refresh_response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        assert refresh_response.status_code in [401, 500]
        
        # 5. Test logout with invalid token (should be graceful)
        logout_response = client.post("/api/v1/auth/logout", json={
            "refresh_token": "invalid_token"
        })
        assert logout_response.status_code == 200  # Should handle gracefully


class TestTokenValidation:
    """Test JWT token validation."""
    
    def test_token_validation_invalid_format(self):
        """Test validation of malformed tokens."""
        from app.core.auth import verify_token
        from jose import JWTError
        
        # Test with invalid token format
        with pytest.raises(JWTError):
            verify_token("invalid.token.format")
    
    def test_token_validation_wrong_signature(self):
        """Test validation of tokens with wrong signature."""
        from app.core.auth import verify_token
        from jose import JWTError
        
        # Create token with wrong signature (using different secret)
        fake_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjo5OTk5OTk5OTk5fQ.Ks_BdfH4CWilyzLNk8S2gDARFhuxIauLNcOWAp0D-NM"
        
        with pytest.raises(JWTError):
            verify_token(fake_token)


class TestSecurityMeasures:
    """Test security measures implementation."""
    
    def test_user_id_type_safety(self):
        """Test that user IDs are properly typed."""
        from app.models.database import User
        
        user = User(
            id="string-id",  # Should be string type
            username="test",
            email="test@example.com", 
            hashed_password="hashed",
            is_active=True,
            is_admin=False
        )
        
        assert isinstance(user.id, str)
        assert len(user.id) > 0
    
    def test_token_expiration_settings(self):
        """Test that token expiration settings are reasonable."""
        from app.core.config import settings
        
        # Access tokens should be short-lived (30 minutes default)
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES <= 60
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0
        
        # Refresh tokens should be longer-lived but not excessive
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS <= 30
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS >= 1
    
    def test_jwt_algorithm_security(self):
        """Test that secure JWT algorithm is used."""
        from app.core.config import settings
        
        # Should use HMAC algorithms for symmetrical key
        assert settings.JWT_ALGORITHM in ["HS256", "HS384", "HS512"]


class TestErrorHandling:
    """Test error handling in authentication."""
    
    def test_authentication_with_malformed_data(self, client):
        """Test authentication with malformed request data."""
        # Missing password field
        response = client.post("/api/v1/auth/login", json={
            "username": "test"
            # missing password
        })
        assert response.status_code in [422, 400]  # Validation error
        
        # Missing username field
        response = client.post("/api/v1/auth/login", json={
            "password": "test"
            # missing username
        })
        assert response.status_code in [422, 400]  # Validation error
    
    def test_refresh_with_malformed_data(self, client):
        """Test refresh endpoint with malformed data."""
        # Missing refresh_token field
        response = client.post("/api/v1/auth/refresh", json={})
        assert response.status_code in [422, 400]  # Validation error
        
        # Wrong field name
        response = client.post("/api/v1/auth/refresh", json={
            "token": "some_token"  # should be refresh_token
        })
        assert response.status_code in [422, 400]  # Validation error


@pytest.fixture
def client():
    """Test client fixture."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    return TestClient(app)
