"""
Engagement service for likes, retweets, and bookmarks.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.user import User
from app.repositories.engagement_repository import EngagementRepository
from app.repositories.tweet_repository import TweetRepository
from app.schemas.common import PaginationMeta
from app.schemas.tweet import (
    QuotedTweetResponse,
    TweetAuthor,
    TweetListResponse,
    TweetResponse,
)


class EngagementService:
    """Service for engagement operations (likes, retweets, bookmarks)."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.engagement_repo = EngagementRepository(db)
        self.tweet_repo = TweetRepository(db)
    
    # Like operations
    async def like_tweet(self, tweet_id: uuid.UUID, current_user: User) -> None:
        """Like a tweet."""
        # Verify tweet exists
        tweet = await self.tweet_repo.get_by_id(tweet_id)
        if not tweet:
            raise NotFoundException("Tweet not found")
        
        # Check if already liked
        existing = await self.engagement_repo.get_like(current_user.id, tweet_id)
        if existing:
            raise BadRequestException("Tweet already liked")
        
        await self.engagement_repo.create_like(current_user.id, tweet_id)
    
    async def unlike_tweet(self, tweet_id: uuid.UUID, current_user: User) -> None:
        """Unlike a tweet."""
        like = await self.engagement_repo.get_like(current_user.id, tweet_id)
        if not like:
            raise NotFoundException("Like not found")
        
        await self.engagement_repo.delete_like(like)
    
    # Retweet operations
    async def retweet(self, tweet_id: uuid.UUID, current_user: User) -> None:
        """Retweet a tweet."""
        # Verify tweet exists
        tweet = await self.tweet_repo.get_by_id(tweet_id)
        if not tweet:
            raise NotFoundException("Tweet not found")
        
        # Can't retweet own tweet
        if tweet.user_id == current_user.id:
            raise BadRequestException("Cannot retweet your own tweet")
        
        # Check if already retweeted
        existing = await self.engagement_repo.get_retweet(current_user.id, tweet_id)
        if existing:
            raise BadRequestException("Tweet already retweeted")
        
        await self.engagement_repo.create_retweet(current_user.id, tweet_id)
    
    async def unretweet(self, tweet_id: uuid.UUID, current_user: User) -> None:
        """Undo a retweet."""
        retweet = await self.engagement_repo.get_retweet(current_user.id, tweet_id)
        if not retweet:
            raise NotFoundException("Retweet not found")
        
        await self.engagement_repo.delete_retweet(retweet)
    
    # Bookmark operations
    async def bookmark_tweet(self, tweet_id: uuid.UUID, current_user: User) -> None:
        """Bookmark a tweet."""
        # Verify tweet exists
        tweet = await self.tweet_repo.get_by_id(tweet_id)
        if not tweet:
            raise NotFoundException("Tweet not found")
        
        # Check if already bookmarked
        existing = await self.engagement_repo.get_bookmark(current_user.id, tweet_id)
        if existing:
            raise BadRequestException("Tweet already bookmarked")
        
        await self.engagement_repo.create_bookmark(current_user.id, tweet_id)
    
    async def unbookmark_tweet(self, tweet_id: uuid.UUID, current_user: User) -> None:
        """Remove a bookmark."""
        bookmark = await self.engagement_repo.get_bookmark(current_user.id, tweet_id)
        if not bookmark:
            raise NotFoundException("Bookmark not found")
        
        await self.engagement_repo.delete_bookmark(bookmark)
    
    async def get_bookmarks(
        self,
        current_user: User,
        page: int = 1,
        limit: int = 20,
    ) -> TweetListResponse:
        """Get paginated bookmarked tweets for current user."""
        offset = (page - 1) * limit
        
        tweets, total_count = await self.engagement_repo.get_user_bookmarks(
            current_user.id, offset, limit
        )
        
        # Build response for each tweet
        tweets_response = []
        for tweet in tweets:
            # Get counts
            data = await self.tweet_repo.get_with_counts(tweet.id, current_user.id)
            if data:
                tweets_response.append(self._build_tweet_response(data))
        
        pagination = PaginationMeta.create(total_count, page, limit)
        
        return TweetListResponse(data=tweets_response, pagination=pagination)
    
    def _build_tweet_response(self, data: dict) -> TweetResponse:
        """Build tweet response from data dict."""
        tweet = data["tweet"]
        
        quoted_tweet_response = None
        if tweet.quoted_tweet:
            qt = tweet.quoted_tweet
            quoted_tweet_response = QuotedTweetResponse(
                id=qt.id,
                content=qt.content,
                image_url=qt.image_url,
                created_at=qt.created_at,
                author=TweetAuthor(
                    id=qt.user.id,
                    username=qt.user.username,
                    display_name=qt.user.display_name,
                    profile_image_url=qt.user.profile_image_url,
                ),
            )
        
        return TweetResponse(
            id=tweet.id,
            content=tweet.content,
            image_url=tweet.image_url,
            views_count=tweet.views_count,
            is_edited=tweet.is_edited,
            created_at=tweet.created_at,
            updated_at=tweet.updated_at,
            author=TweetAuthor(
                id=tweet.user.id,
                username=tweet.user.username,
                display_name=tweet.user.display_name,
                profile_image_url=tweet.user.profile_image_url,
            ),
            quoted_tweet=quoted_tweet_response,
            likes_count=data["likes_count"],
            comments_count=data["comments_count"],
            retweets_count=data["retweets_count"],
            is_liked=data["is_liked"],
            is_retweeted=data["is_retweeted"],
            is_bookmarked=data["is_bookmarked"],
        )
