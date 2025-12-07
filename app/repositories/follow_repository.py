"""
Follow repository for database operations.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.follow import Follow
from app.models.user import User


class FollowRepository:
    """Repository for follow operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_follow(
        self,
        follower_id: uuid.UUID,
        following_id: uuid.UUID,
    ) -> Follow | None:
        """Get a follow relationship."""
        result = await self.db.execute(
            select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def create_follow(
        self,
        follower_id: uuid.UUID,
        following_id: uuid.UUID,
    ) -> Follow:
        """Create a new follow relationship."""
        follow = Follow(follower_id=follower_id, following_id=following_id)
        self.db.add(follow)
        await self.db.flush()
        await self.db.refresh(follow)
        return follow
    
    async def delete_follow(self, follow: Follow) -> None:
        """Delete a follow relationship."""
        await self.db.delete(follow)
        await self.db.flush()
    
    async def get_followers_count(self, user_id: uuid.UUID) -> int:
        """Get the number of followers for a user."""
        result = await self.db.execute(
            select(func.count(Follow.id)).where(Follow.following_id == user_id)
        )
        return result.scalar() or 0
    
    async def get_following_count(self, user_id: uuid.UUID) -> int:
        """Get the number of users a user is following."""
        result = await self.db.execute(
            select(func.count(Follow.id)).where(Follow.follower_id == user_id)
        )
        return result.scalar() or 0
    
    async def get_followers(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        """Get paginated list of followers."""
        # Count
        count_result = await self.db.execute(
            select(func.count(Follow.id)).where(Follow.following_id == user_id)
        )
        total_count = count_result.scalar() or 0
        
        # Data
        result = await self.db.execute(
            select(Follow)
            .options(joinedload(Follow.follower))
            .where(Follow.following_id == user_id)
            .order_by(Follow.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        follows = result.unique().scalars().all()
        users = [follow.follower for follow in follows]
        
        return users, total_count
    
    async def get_following(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        """Get paginated list of users being followed."""
        # Count
        count_result = await self.db.execute(
            select(func.count(Follow.id)).where(Follow.follower_id == user_id)
        )
        total_count = count_result.scalar() or 0
        
        # Data
        result = await self.db.execute(
            select(Follow)
            .options(joinedload(Follow.following))
            .where(Follow.follower_id == user_id)
            .order_by(Follow.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        follows = result.unique().scalars().all()
        users = [follow.following for follow in follows]
        
        return users, total_count
    
    async def is_following(
        self,
        follower_id: uuid.UUID,
        following_id: uuid.UUID,
    ) -> bool:
        """Check if a user is following another user."""
        follow = await self.get_follow(follower_id, following_id)
        return follow is not None
