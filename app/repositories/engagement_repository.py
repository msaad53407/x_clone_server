"""
Engagement repository for likes and bookmarks.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.bookmark import Bookmark
from app.models.like import Like
from app.models.tweet import Tweet


class EngagementRepository:
    """Repository for engagement operations (likes, bookmarks)."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Like operations
    async def get_like(self, user_id: uuid.UUID, tweet_id: uuid.UUID) -> Like | None:
        """Get a like by user and tweet."""
        result = await self.db.execute(
            select(Like).where(
                Like.user_id == user_id,
                Like.tweet_id == tweet_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def create_like(self, user_id: uuid.UUID, tweet_id: uuid.UUID) -> Like:
        """Create a new like."""
        like = Like(user_id=user_id, tweet_id=tweet_id)
        self.db.add(like)
        await self.db.flush()
        await self.db.refresh(like)
        return like
    
    async def delete_like(self, like: Like) -> None:
        """Delete a like."""
        await self.db.delete(like)
        await self.db.flush()
    
    # Bookmark operations
    async def get_bookmark(self, user_id: uuid.UUID, tweet_id: uuid.UUID) -> Bookmark | None:
        """Get a bookmark by user and tweet."""
        result = await self.db.execute(
            select(Bookmark).where(
                Bookmark.user_id == user_id,
                Bookmark.tweet_id == tweet_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def create_bookmark(self, user_id: uuid.UUID, tweet_id: uuid.UUID) -> Bookmark:
        """Create a new bookmark."""
        bookmark = Bookmark(user_id=user_id, tweet_id=tweet_id)
        self.db.add(bookmark)
        await self.db.flush()
        await self.db.refresh(bookmark)
        return bookmark
    
    async def delete_bookmark(self, bookmark: Bookmark) -> None:
        """Delete a bookmark."""
        await self.db.delete(bookmark)
        await self.db.flush()
    
    async def get_user_bookmarks(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Tweet], int]:
        """Get paginated bookmarked tweets for a user."""
        # Count query
        count_result = await self.db.execute(
            select(func.count(Bookmark.id)).where(Bookmark.user_id == user_id)
        )
        total_count = count_result.scalar() or 0
        
        # Data query - get bookmarks with tweets
        result = await self.db.execute(
            select(Bookmark)
            .options(
                joinedload(Bookmark.tweet).joinedload(Tweet.user),
                joinedload(Bookmark.tweet).joinedload(Tweet.quoted_tweet).joinedload(Tweet.user),
            )
            .where(Bookmark.user_id == user_id)
            .order_by(Bookmark.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        bookmarks = result.unique().scalars().all()
        tweets = [bookmark.tweet for bookmark in bookmarks]
        
        return tweets, total_count
