"""
Token repository for database operations on various token types.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_verification_token import EmailVerificationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken


class TokenRepository:
    """Repository for token database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Email Verification Token Methods
    
    async def create_email_verification_token(
        self,
        user_id: uuid.UUID,
        token: str,
        expires_in_hours: int = 24,
    ) -> EmailVerificationToken:
        """
        Create a new email verification token.
        
        Args:
            user_id: UUID of the user
            token: Token string
            expires_in_hours: Hours until token expires
            
        Returns:
            Created token instance
        """
        # Delete any existing tokens for this user
        await self.db.execute(
            delete(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id
            )
        )
        
        verification_token = EmailVerificationToken(
            user_id=user_id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
        )
        self.db.add(verification_token)
        await self.db.flush()
        await self.db.refresh(verification_token)
        return verification_token
    
    async def get_email_verification_token(self, token: str) -> EmailVerificationToken | None:
        """
        Get an email verification token by its value.
        
        Args:
            token: Token string to look up
            
        Returns:
            Token instance or None if not found
        """
        result = await self.db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token == token
            )
        )
        return result.scalar_one_or_none()
    
    async def delete_email_verification_token(self, token: EmailVerificationToken) -> None:
        """Delete an email verification token."""
        await self.db.delete(token)
        await self.db.flush()
    
    # Password Reset Token Methods
    
    async def create_password_reset_token(
        self,
        user_id: uuid.UUID,
        token: str,
        expires_in_hours: int = 1,
    ) -> PasswordResetToken:
        """
        Create a new password reset token.
        
        Args:
            user_id: UUID of the user
            token: Token string
            expires_in_hours: Hours until token expires
            
        Returns:
            Created token instance
        """
        # Delete any existing tokens for this user
        await self.db.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.user_id == user_id
            )
        )
        
        reset_token = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
        )
        self.db.add(reset_token)
        await self.db.flush()
        await self.db.refresh(reset_token)
        return reset_token
    
    async def get_password_reset_token(self, token: str) -> PasswordResetToken | None:
        """
        Get a password reset token by its value.
        
        Args:
            token: Token string to look up
            
        Returns:
            Token instance or None if not found
        """
        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token == token
            )
        )
        return result.scalar_one_or_none()
    
    async def mark_password_reset_token_used(self, token: PasswordResetToken) -> None:
        """Mark a password reset token as used."""
        token.used = True
        await self.db.flush()
    
    # Refresh Token Methods
    
    async def create_refresh_token(
        self,
        user_id: uuid.UUID,
        token: str,
        expires_in_days: int = 7,
    ) -> RefreshToken:
        """
        Create a new refresh token.
        
        Args:
            user_id: UUID of the user
            token: Token string
            expires_in_days: Days until token expires
            
        Returns:
            Created token instance
        """
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days),
        )
        self.db.add(refresh_token)
        await self.db.flush()
        await self.db.refresh(refresh_token)
        return refresh_token
    
    async def get_refresh_token(self, token: str) -> RefreshToken | None:
        """
        Get a refresh token by its value.
        
        Args:
            token: Token string to look up
            
        Returns:
            Token instance or None if not found
        """
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()
    
    async def revoke_refresh_token(self, token: RefreshToken) -> None:
        """Revoke a refresh token."""
        token.revoked = True
        await self.db.flush()
    
    async def revoke_all_user_refresh_tokens(self, user_id: uuid.UUID) -> None:
        """Revoke all refresh tokens for a user."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,  # noqa: E712
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.revoked = True
        await self.db.flush()
