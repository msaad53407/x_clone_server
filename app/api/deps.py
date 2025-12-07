"""
Shared API dependencies.
"""

import uuid
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import verify_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Args:
        authorization: Bearer token from Authorization header
        db: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        UnauthorizedException: If token is missing, invalid, or user not found
    """
    if not authorization:
        raise UnauthorizedException("Missing authorization header")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedException("Invalid authorization header format")
    
    token = parts[1]
    
    # Verify token
    payload = verify_access_token(token)
    if not payload:
        raise UnauthorizedException("Invalid or expired access token")
    
    # Get user from database
    user_id = uuid.UUID(payload["sub"])
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise UnauthorizedException("User not found")
    
    if not user.is_verified:
        raise UnauthorizedException("Email not verified")
    
    return user


async def get_current_user_optional(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Dependency to get the current user if authenticated, otherwise None.
    Useful for endpoints that have different behavior for authenticated vs anonymous users.
    
    Args:
        authorization: Bearer token from Authorization header
        db: Database session
        
    Returns:
        Current authenticated user or None
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization, db)
    except UnauthorizedException:
        return None


# Type aliases for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
