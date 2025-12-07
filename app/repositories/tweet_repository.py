"""
Tweet repository for database operations on tweets.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.bookmark import Bookmark
from app.models.comment import Comment
from app.models.like import Like
from app.models.tweet import Tweet


class TweetRepository:
    """Repository for tweet database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, tweet: Tweet) -> Tweet:
        """Create a new tweet."""
        self.db.add(tweet)
        await self.db.flush()
        await self.db.refresh(tweet)
        return tweet
    
    async def get_by_id(self, tweet_id: uuid.UUID) -> Tweet | None:
        """Get a tweet by ID with author loaded."""
        result = await self.db.execute(
            select(Tweet)
            .options(
                joinedload(Tweet.user),
                joinedload(Tweet.quoted_tweet).joinedload(Tweet.user),
            )
            .where(Tweet.id == tweet_id)
        )
        return result.unique().scalar_one_or_none()
    
    async def get_with_counts(
        self,
        tweet_id: uuid.UUID,
        current_user_id: uuid.UUID | None = None,
    ) -> dict | None:
        """Get tweet with engagement counts and user interaction status."""
        tweet = await self.get_by_id(tweet_id)
        if not tweet:
            return None
        
        # Get counts
        likes_count = await self._get_likes_count(tweet_id)
        comments_count = await self._get_comments_count(tweet_id)
        
        # Get user interaction status
        is_liked = False
        is_bookmarked = False
        
        if current_user_id:
            is_liked = await self._is_liked_by_user(tweet_id, current_user_id)
            is_bookmarked = await self._is_bookmarked_by_user(tweet_id, current_user_id)
        
        return {
            "tweet": tweet,
            "likes_count": likes_count,
            "comments_count": comments_count,
            "is_liked": is_liked,
            "is_bookmarked": is_bookmarked,
        }
    
    async def get_list(
        self,
        offset: int = 0,
        limit: int = 20,
        user_id: uuid.UUID | None = None,
        current_user_id: uuid.UUID | None = None,
    ) -> tuple[list[dict], int]:
        """
        Get paginated list of tweets with counts.
        
        Args:
            offset: Pagination offset
            limit: Number of items to return
            user_id: Filter by user (for profile page)
            current_user_id: Current user for interaction status
            
        Returns:
            Tuple of (tweets with counts, total count)
        """
        # Base query
        query = (
            select(Tweet)
            .options(
                joinedload(Tweet.user),
                joinedload(Tweet.quoted_tweet).joinedload(Tweet.user),
            )
            .order_by(Tweet.created_at.desc())
        )
        
        # Count query
        count_query = select(func.count(Tweet.id))
        
        if user_id:
            query = query.where(Tweet.user_id == user_id)
            count_query = count_query.where(Tweet.user_id == user_id)
        
        # Get total count
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Get tweets
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        tweets = result.unique().scalars().all()
        
        # Get counts and interaction status for each tweet
        tweets_with_counts = []
        for tweet in tweets:
            likes_count = await self._get_likes_count(tweet.id)
            comments_count = await self._get_comments_count(tweet.id)
            
            is_liked = False
            is_bookmarked = False
            
            if current_user_id:
                is_liked = await self._is_liked_by_user(tweet.id, current_user_id)
                is_bookmarked = await self._is_bookmarked_by_user(tweet.id, current_user_id)
            
            tweets_with_counts.append({
                "tweet": tweet,
                "likes_count": likes_count,
                "comments_count": comments_count,
                "is_liked": is_liked,
                "is_bookmarked": is_bookmarked,
            })
        
        return tweets_with_counts, total_count
    
    async def update(self, tweet: Tweet) -> Tweet:
        """Update a tweet."""
        tweet.is_edited = True
        tweet.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(tweet)
        return tweet
    
    async def delete(self, tweet: Tweet) -> None:
        """Delete a tweet."""
        await self.db.delete(tweet)
        await self.db.flush()
    
    async def increment_views(self, tweet_id: uuid.UUID) -> None:
        """Increment view count for a tweet."""
        tweet = await self.get_by_id(tweet_id)
        if tweet:
            tweet.views_count += 1
            await self.db.flush()
    
    # Helper methods for counts
    async def _get_likes_count(self, tweet_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count(Like.id)).where(Like.tweet_id == tweet_id)
        )
        return result.scalar() or 0
    
    async def _get_comments_count(self, tweet_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count(Comment.id)).where(Comment.tweet_id == tweet_id)
        )
        return result.scalar() or 0
    
    async def _is_liked_by_user(self, tweet_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(Like.id).where(
                Like.tweet_id == tweet_id,
                Like.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def _is_bookmarked_by_user(self, tweet_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(Bookmark.id).where(
                Bookmark.tweet_id == tweet_id,
                Bookmark.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None
