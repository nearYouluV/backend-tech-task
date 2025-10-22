"""
JWT authentication utilities with refresh token support.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, Tuple
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from ..core.config import settings
from ..models.database import User, RefreshToken
from ..database.connection import get_db

# OAuth2 scheme for token authentication
oauth2_scheme = HTTPBearer()


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storing in the database."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "jti": str(uuid4()), "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token() -> str:
    """Create a cryptographically secure refresh token."""
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    """Hash a token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def store_refresh_token(db: AsyncSession, user_id: str, refresh_token: str) -> RefreshToken:
    """Store refresh token in database."""
    token_hash = hash_token(refresh_token)
    expires_at = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Revoke all existing refresh tokens for this user
    await revoke_user_refresh_tokens(db, user_id)
    
    db_token = RefreshToken(
        id=str(uuid4()),
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    
    return db_token


async def get_refresh_token(db: AsyncSession, token: str) -> Optional[RefreshToken]:
    """Get refresh token by token value if it's valid and not expired."""
    token_hash = hash_token(token)
    
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expires_at > datetime.now(UTC),
            RefreshToken.is_revoked == False
        )
    )
    return result.scalar_one_or_none()


async def revoke_refresh_token(db: AsyncSession, refresh_token: str) -> bool:
    """Revoke a specific refresh token."""
    token_hash = hash_token(refresh_token)
    
    result = await db.execute(
        select(RefreshToken).filter(RefreshToken.token_hash == token_hash)
    )
    
    db_token = result.scalar_one_or_none()
    if db_token:
        db_token.is_revoked = True
        await db.commit()
        return True
    
    return False


async def revoke_user_refresh_tokens(db: AsyncSession, user_id: int) -> int:
    """Revoke all refresh tokens for a user."""
    result = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
        .values(is_revoked=True)
    )
    await db.commit()
    return result.rowcount


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """Clean up expired refresh tokens from database."""
    result = await db.execute(
        delete(RefreshToken).filter(RefreshToken.expires_at < datetime.now(UTC))
    )
    
    await db.commit()
    return result.rowcount


async def create_token_pair(db: AsyncSession, user: User) -> Tuple[str, str]:
    """Create access and refresh token pair."""
    # Create access token
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username}
    )
    
    # Create and store refresh token
    refresh_token = create_refresh_token()
    await store_refresh_token(db, user.id, refresh_token)
    
    return access_token, refresh_token


def verify_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Check token type
        token_type = payload.get("type", "access")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}, got {token_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password."""
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
        
    return user


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username."""
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """Get user by ID."""
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, username: str, email: str, password: str, is_admin: bool = False) -> User:
    """Create a new user."""
    hashed_password = get_password_hash(password)
    
    user = User(
        id=str(uuid4()),
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_admin=is_admin
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
