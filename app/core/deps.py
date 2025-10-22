"""
Authentication dependencies and middleware.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_db
from ..core.auth import verify_token, get_user_by_id
from ..models.database import User
from ..schemas.auth import TokenData


# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id)
    except Exception:
        raise credentials_exception
    
    # Get user from database
    user = await get_user_by_id(db, user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_optional_current_user():
    """Optional authentication - returns None if no token provided."""
    async def _get_optional_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: AsyncSession = Depends(get_db)
    ) -> Optional[User]:
        if not credentials:
            return None
            
        try:
            payload = verify_token(credentials.credentials)
            user_id: str = payload.get("sub")
            
            if user_id is None:
                return None
                
            user = await get_user_by_id(db, user_id=user_id)
            return user if user and user.is_active else None
            
        except Exception:
            return None
    
    return _get_optional_user
