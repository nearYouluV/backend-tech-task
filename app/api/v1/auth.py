"""
Authentication API endpoints.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import get_db
from app.core.auth import (
    verify_password, create_access_token, create_token_pair,
    get_current_active_user, store_refresh_token, revoke_refresh_token,
    get_refresh_token, revoke_user_refresh_tokens,
    get_user_by_username, get_user_by_id, create_user, authenticate_user
)
from ...core.config import settings
from ...core.deps import get_current_active_user, get_current_admin_user
from ...schemas.auth import LoginRequest, Token, UserCreate, UserSignup, UserResponse, RefreshTokenRequest, LogoutRequest, GrantAdminRequest
from ...models.database import User


router = APIRouter()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup_user(
    user_data: UserSignup,
    db: AsyncSession = Depends(get_db)
):
    """
    Public user registration.
    
    - **username**: Unique username
    - **email**: User email address  
    - **password**: User password (will be hashed)
    
    Note: All new users are created as regular users (not admins).
    """
    # Check if user already exists
    existing_user = await get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user (always as regular user)
    user = await create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        is_admin=False  # Public signup always creates regular users
    )
    
    return user



@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login and get access token.
    
    - **username**: User username
    - **password**: User password
    
    Returns JWT access token that expires in 30 minutes.
    """
    # Authenticate user
    user = await authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token pair
    access_token, refresh_token = await create_token_pair(db, user)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.
    
    Requires valid JWT token in Authorization header.
    """
    return current_user


@router.post("/grant-admin", response_model=UserResponse)
async def grant_admin_privileges(
    grant_request: GrantAdminRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Grant admin privileges to a user (admin only).
    
    - **username**: Username of the user to grant admin privileges
    
    Only existing admins can grant admin privileges to other users.
    """
    # Find the user to grant admin privileges
    user = await get_user_by_username(db, grant_request.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has admin privileges"
        )
    
    # Grant admin privileges
    user.is_admin = True
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access and refresh token pair.
    """
    # Validate refresh token
    db_refresh_token = await get_refresh_token(db, refresh_request.refresh_token)
    if not db_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user
    user = await get_user_by_id(db, db_refresh_token.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Revoke old refresh token and create new pair
    await revoke_refresh_token(db, refresh_request.refresh_token)
    access_token, new_refresh_token = await create_token_pair(db, user)
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    logout_request: LogoutRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user by revoking refresh token.
    
    - **refresh_token**: Refresh token to revoke
    """
    revoked = await revoke_refresh_token(db, logout_request.refresh_token)
    
    return {
        "message": "Successfully logged out" if revoked else "Token already invalid",
        "revoked": revoked
    }


@router.post("/logout-all", status_code=status.HTTP_200_OK)
async def logout_all(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout from all devices by revoking all refresh tokens.
    
    Requires valid JWT token in Authorization header.
    """
    count = await revoke_user_refresh_tokens(db, current_user.id)
    
    return {
        "message": f"Successfully logged out from {count} device(s)",
        "revoked_tokens": count
    }


@router.get("/health")
async def auth_health():
    """Health check for auth service."""
    return {
        "status": "healthy",
        "service": "authentication",
        "jwt_algorithm": settings.JWT_ALGORITHM,
        "access_token_expire_minutes": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        "refresh_token_expire_days": settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    }
