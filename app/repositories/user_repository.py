"""
User repository for database operations on users.
"""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.follow import Follow


class UserRepository:
    """Repository for user database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, user: User) -> User:
        """
        Create a new user in the database.
        
        Args:
            user: User model instance to create
            
        Returns:
            Created user instance
        """
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """
        Get a user by their ID.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            User instance or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> User | None:
        """
        Get a user by their email address.
        
        Args:
            email: Email address of the user
            
        Returns:
            User instance or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> User | None:
        """
        Get a user by their username.
        
        Args:
            username: Username of the user
            
        Returns:
            User instance or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.username == username.lower())
        )
        return result.scalar_one_or_none()
    
    async def update(self, user: User) -> User:
        """
        Update a user in the database.
        
        Args:
            user: User model instance with updated fields
            
        Returns:
            Updated user instance
        """
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user: User) -> None:
        """
        Delete a user from the database.
        
        Args:
            user: User model instance to delete
        """
        await self.db.delete(user)
        await self.db.flush()
    
    async def exists_by_email(self, email: str) -> bool:
        """
        Check if a user exists with the given email.
        
        Args:
            email: Email address to check
            
        Returns:
            True if user exists, False otherwise
        """
        result = await self.db.execute(
            select(User.id).where(User.email == email.lower())
        )
        return result.scalar_one_or_none() is not None
    
    async def exists_by_username(self, username: str) -> bool:
        """
        Check if a user exists with the given username.
        
        Args:
            username: Username to check
            
        Returns:
            True if user exists, False otherwise
        """
        result = await self.db.execute(
            select(User.id).where(User.username == username.lower())
        )
        return result.scalar_one_or_none() is not None
    
    async def verify_email(self, user: User) -> User:
        """
        Mark a user's email as verified.
        
        Args:
            user: User model instance to verify
            
        Returns:
            Updated user instance
        """
        user.is_verified = True
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def get_users_not_followed_by(
        self, 
        user_id: uuid.UUID, 
        limit: int = 3
    ) -> list[User]:
        """
        Get users that the given user is not following.
        
        Args:
            user_id: ID of the user to find suggestions for
            limit: Maximum number of users to return
            
        Returns:
            List of users not followed by the given user
        """
        # Subquery to get IDs of users that current user is following
        following_subquery = (
            select(Follow.following_id)
            .where(Follow.follower_id == user_id)
        )
        
        # Get users that are not followed and not the current user
        result = await self.db.execute(
            select(User)
            .where(User.id != user_id)
            .where(User.id.notin_(following_subquery))
            .order_by(func.random())
            .limit(limit)
        )
        return list(result.scalars().all())

