"""
Authentication service for user registration, login, and token management.
"""

import secrets
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_refresh_token,
)
from app.models.user import User
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.email_service import email_service


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = TokenRepository(db)
    
    async def register(self, user_data: UserCreate) -> UserResponse:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            Created user response
            
        Raises:
            ConflictException: If email or username already exists
        """
        # Check if email already exists
        if await self.user_repo.exists_by_email(user_data.email):
            raise ConflictException("Email already registered")
        
        # Check if username already exists
        if await self.user_repo.exists_by_username(user_data.username):
            raise ConflictException("Username already taken")
        
        # Create user with hashed password
        user = User(
            username=user_data.username.lower(),
            email=user_data.email.lower(),
            password_hash=get_password_hash(user_data.password),
            display_name=user_data.display_name or user_data.username,
            is_verified=False,
        )
        
        user = await self.user_repo.create(user)
        
        # Create email verification token
        verification_token = secrets.token_urlsafe(32)
        await self.token_repo.create_email_verification_token(
            user_id=user.id,
            token=verification_token,
        )
        
        # Send verification email (async, don't wait)
        await email_service.send_verification_email(
            email=user.email,
            username=user.username,
            token=verification_token,
        )
        
        return UserResponse.model_validate(user)
    
    async def login(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate user and return tokens.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Token response with access and refresh tokens
            
        Raises:
            UnauthorizedException: If credentials are invalid
            BadRequestException: If email is not verified
        """
        user = await self.user_repo.get_by_email(email)
        
        if not user:
            raise UnauthorizedException("Invalid email or password")
        
        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")
        
        if not user.is_verified:
            raise BadRequestException(
                "Email not verified. Please check your email for verification link."
            )
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Store refresh token in database
        await self.token_repo.create_refresh_token(
            user_id=user.id,
            token=refresh_token,
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    
    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New token response
            
        Raises:
            UnauthorizedException: If refresh token is invalid
        """
        # Verify JWT token
        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise UnauthorizedException("Invalid refresh token")
        
        # Check token in database
        stored_token = await self.token_repo.get_refresh_token(refresh_token)
        if not stored_token or not stored_token.is_valid:
            raise UnauthorizedException("Invalid or expired refresh token")
        
        user_id = uuid.UUID(payload["sub"])
        user = await self.user_repo.get_by_id(user_id)
        
        if not user:
            raise UnauthorizedException("User not found")
        
        # Revoke old refresh token
        await self.token_repo.revoke_refresh_token(stored_token)
        
        # Create new tokens
        new_access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Store new refresh token
        await self.token_repo.create_refresh_token(
            user_id=user.id,
            token=new_refresh_token,
        )
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )
    
    async def logout(self, refresh_token: str) -> None:
        """
        Logout user by revoking refresh token.
        
        Args:
            refresh_token: Refresh token to revoke
        """
        stored_token = await self.token_repo.get_refresh_token(refresh_token)
        if stored_token:
            await self.token_repo.revoke_refresh_token(stored_token)
    
    async def verify_email(self, token: str) -> UserResponse:
        """
        Verify user's email address.
        
        Args:
            token: Email verification token
            
        Returns:
            Updated user response
            
        Raises:
            BadRequestException: If token is invalid or expired
        """
        stored_token = await self.token_repo.get_email_verification_token(token)
        
        if not stored_token:
            raise BadRequestException("Invalid verification token")
        
        if stored_token.is_expired:
            await self.token_repo.delete_email_verification_token(stored_token)
            raise BadRequestException("Verification token has expired")
        
        user = await self.user_repo.get_by_id(stored_token.user_id)
        if not user:
            raise NotFoundException("User not found")
        
        if user.is_verified:
            raise BadRequestException("Email already verified")
        
        # Mark user as verified
        user = await self.user_repo.verify_email(user)
        
        # Delete the token
        await self.token_repo.delete_email_verification_token(stored_token)
        
        return UserResponse.model_validate(user)
    
    async def resend_verification_email(self, email: str) -> None:
        """
        Resend verification email.
        
        Args:
            email: User's email address
            
        Raises:
            NotFoundException: If user not found
            BadRequestException: If email already verified
        """
        user = await self.user_repo.get_by_email(email)
        
        if not user:
            raise NotFoundException("User not found")
        
        if user.is_verified:
            raise BadRequestException("Email already verified")
        
        # Create new verification token
        verification_token = secrets.token_urlsafe(32)
        await self.token_repo.create_email_verification_token(
            user_id=user.id,
            token=verification_token,
        )
        
        # Send verification email
        await email_service.send_verification_email(
            email=user.email,
            username=user.username,
            token=verification_token,
        )
    
    async def forgot_password(self, email: str) -> None:
        """
        Send password reset email.
        
        Args:
            email: User's email address
        """
        user = await self.user_repo.get_by_email(email)
        
        # Don't reveal if user exists or not
        if not user:
            return
        
        # Create password reset token
        reset_token = secrets.token_urlsafe(32)
        await self.token_repo.create_password_reset_token(
            user_id=user.id,
            token=reset_token,
        )
        
        # Send reset email
        await email_service.send_password_reset_email(
            email=user.email,
            username=user.username,
            token=reset_token,
        )
    
    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset user's password.
        
        Args:
            token: Password reset token
            new_password: New password
            
        Raises:
            BadRequestException: If token is invalid or expired
        """
        stored_token = await self.token_repo.get_password_reset_token(token)
        
        if not stored_token:
            raise BadRequestException("Invalid reset token")
        
        if not stored_token.is_valid:
            raise BadRequestException("Reset token has expired or already been used")
        
        user = await self.user_repo.get_by_id(stored_token.user_id)
        if not user:
            raise NotFoundException("User not found")
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        await self.user_repo.update(user)
        
        # Mark token as used
        await self.token_repo.mark_password_reset_token_used(stored_token)
        
        # Revoke all refresh tokens for security
        await self.token_repo.revoke_all_user_refresh_tokens(user.id)
