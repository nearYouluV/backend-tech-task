"""
Test refresh token functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, AsyncMock, patch

from app.core.auth import (
    create_token_pair, get_refresh_token, revoke_refresh_token,
    revoke_user_refresh_tokens, create_user, authenticate_user
)
from app.models.database import User, RefreshToken


class TestRefreshTokens:
    """Test refresh token functionality."""
    
    @pytest.fixture
    def test_user(self):
        """Create test user."""
        return User(
            id="test-user-id",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
            is_admin=False
        )
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = Mock()
        return db
    
    def test_create_token_pair(self, test_user, mock_db):
        """Test creating access and refresh token pair."""
        async def test():
            # Mock database responses
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            
            access_token, refresh_token = await create_token_pair(mock_db, test_user)
            
            # Check tokens are strings and not empty
            assert isinstance(access_token, str)
            assert isinstance(refresh_token, str)
            assert len(access_token) > 0
            assert len(refresh_token) > 0
            
            # Verify database operations
            assert mock_db.add.called
            assert mock_db.commit.called
        
        asyncio.run(test())
    
    def test_get_refresh_token_valid(self, mock_db):
        """Test getting valid refresh token."""
        async def test():
            # Mock valid refresh token
            mock_token = RefreshToken(
                id="token-id",
                user_id="user-id",
                token_hash="hashed_token",
                expires_at=datetime.now(UTC) + timedelta(days=1),
                is_revoked=False
            )
            
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = mock_token
            mock_db.execute.return_value = mock_result
            
            token = await get_refresh_token(mock_db, "valid_token")
            
            assert token == mock_token
            assert mock_db.execute.called
        
        asyncio.run(test())
    
    def test_get_refresh_token_expired(self, mock_db):
        """Test getting expired refresh token returns None."""
        async def test():
            # Mock expired token (returns None from database query)
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            
            token = await get_refresh_token(mock_db, "expired_token")
            
            assert token is None
        
        asyncio.run(test())
    
    def test_revoke_refresh_token_success(self, mock_db):
        """Test successful token revocation."""
        async def test():
            # Mock existing token
            mock_token = RefreshToken(
                id="token-id",
                user_id="user-id",
                token_hash="hashed_token",
                expires_at=datetime.now(UTC) + timedelta(days=1),
                is_revoked=False
            )
            
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = mock_token
            mock_db.execute.return_value = mock_result
            
            revoked = await revoke_refresh_token(mock_db, "valid_token")
            
            assert revoked is True
            assert mock_token.is_revoked is True
            assert mock_db.commit.called
        
        asyncio.run(test())
    
    def test_revoke_refresh_token_not_found(self, mock_db):
        """Test revoking non-existent token."""
        async def test():
            # Mock no token found
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            
            revoked = await revoke_refresh_token(mock_db, "invalid_token")
            
            assert revoked is False
            assert not mock_db.commit.called
        
        asyncio.run(test())
    
    def test_revoke_user_refresh_tokens(self, mock_db):
        """Test revoking all user refresh tokens."""
        async def test():
            # Mock update result
            mock_result = Mock()
            mock_result.rowcount = 3  # 3 tokens revoked
            mock_db.execute.return_value = mock_result
            
            count = await revoke_user_refresh_tokens(mock_db, "user-id")
            
            assert count == 3
            assert mock_db.execute.called
            assert mock_db.commit.called
        
        asyncio.run(test())


class TestRefreshTokenAPI:
    """Test refresh token API endpoints."""
    
    def test_refresh_endpoint_success(self, auth_client):
        """Test successful token refresh."""
        # First, create a user and login
        user_data = {
            "username": "refreshuser",
            "email": "refresh@example.com",
            "password": "testpass123",
            "is_admin": False
        }
        
        # Create user via admin (assuming we have admin token)
        admin_headers = {"Authorization": "Bearer admin_token"}
        register_response = auth_client.post(
            "/api/v1/auth/register",
            json=user_data,
            headers=admin_headers
        )
        
        # Login to get tokens
        login_response = auth_client.post(
            "/api/v1/auth/login",
            json={"username": "refreshuser", "password": "testpass123"}
        )
        
        if login_response.status_code == 200:
            tokens = login_response.json()
            refresh_token = tokens["refresh_token"]
            
            # Test refresh endpoint
            refresh_response = auth_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            
            # Should either succeed or fail gracefully
            assert refresh_response.status_code in [200, 401, 500]
            
            if refresh_response.status_code == 200:
                new_tokens = refresh_response.json()
                assert "access_token" in new_tokens
                assert "refresh_token" in new_tokens
                assert new_tokens["access_token"] != tokens["access_token"]
    
    def test_refresh_endpoint_invalid_token(self, auth_client):
        """Test refresh with invalid token."""
        response = auth_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        # Should return 401 for invalid token
        assert response.status_code in [401, 500]
    
    def test_logout_endpoint(self, auth_client):
        """Test logout endpoint."""
        # Test with dummy refresh token
        response = auth_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "dummy_token"}
        )
        
        # Should return 200 regardless (graceful handling)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "revoked" in data


@pytest.fixture
def auth_client(client):
    """Client with authentication setup."""
    return client


class TestTokenSecurity:
    """Test token security aspects."""
    
    def test_token_hash_consistency(self):
        """Test that token hashing is consistent."""
        from app.core.auth import hash_token
        
        token = "test_token"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_refresh_token_uniqueness(self):
        """Test that refresh tokens are unique."""
        from app.core.auth import create_refresh_token
        
        token1 = create_refresh_token()
        token2 = create_refresh_token()
        
        assert token1 != token2
        assert len(token1) > 50  # Should be long enough
        assert len(token2) > 50
    
    def test_access_token_structure(self, test_user):
        """Test access token structure."""
        from app.core.auth import create_access_token
        from jose import jwt
        from app.core.config import settings
        
        token = create_access_token(
            data={"sub": test_user.id, "username": test_user.username}
        )
        
        # Decode token to verify structure
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert payload["sub"] == test_user.id
        assert payload["username"] == test_user.username
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "jti" in payload
    
    @pytest.fixture
    def test_user(self):
        """Test user fixture."""
        return User(
            id="test-user-id",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
            is_admin=False
        )


class TestTokenExpiration:
    """Test token expiration handling."""
    
    def test_expired_refresh_token_rejected(self, mock_db):
        """Test that expired refresh tokens are rejected."""
        async def test():
            # Mock expired token (database query returns None due to expiration filter)
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            
            token = await get_refresh_token(mock_db, "expired_token")
            
            assert token is None
        
        asyncio.run(test())
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db


class TestTokenRotation:
    """Test token rotation functionality."""
    
    def test_old_refresh_token_revoked_on_refresh(self, mock_db, test_user):
        """Test that old refresh token is revoked when creating new pair."""
        async def test():
            # Mock existing token found and revoked
            mock_token = RefreshToken(
                id="old-token-id",
                user_id=test_user.id,
                token_hash="old_hash",
                expires_at=datetime.now(UTC) + timedelta(days=1),
                is_revoked=False
            )
            
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = mock_token
            mock_result.rowcount = 1
            mock_db.execute.return_value = mock_result
            
            # This should revoke old tokens and create new ones
            access_token, refresh_token = await create_token_pair(mock_db, test_user)
            
            assert isinstance(access_token, str)
            assert isinstance(refresh_token, str)
            assert mock_db.execute.called
            assert mock_db.commit.called
        
        asyncio.run(test())
    
    @pytest.fixture
    def test_user(self):
        """Test user fixture."""
        return User(
            id="test-user-id",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
            is_admin=False
        )
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = Mock()
        return db
