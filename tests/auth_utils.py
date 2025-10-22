"""
Test utilities for authentication.
"""

from typing import Dict, Optional
from fastapi.testclient import TestClient

from app.core.auth import create_access_token, get_password_hash
from app.models.database import User


def create_test_user(
    session,
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "testpass123",
    is_admin: bool = False,
    user_id: str = "test-user-id"
) -> User:
    """Create a test user in the database."""
    user = User(
        id=user_id,
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        is_admin=is_admin,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_auth_headers(user: User) -> Dict[str, str]:
    """Get authorization headers for a user."""
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username}
    )
    return {"Authorization": f"Bearer {access_token}"}


def login_user(client: TestClient, username: str, password: str) -> Optional[str]:
    """Login user and return access token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password}
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def create_authenticated_client(client: TestClient, user: User) -> Dict[str, str]:
    """Get authentication headers for making authenticated requests."""
    return get_auth_headers(user)
