"""
Tweet service for business logic operations on tweets.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.tweet import Tweet
from app.models.user import User
from app.repositories.tweet_repository import TweetRepository
from app.schemas.common import PaginationMeta
from app.schemas.tweet import (
    QuotedTweetResponse,
    TweetAuthor,
    TweetCreate,
    TweetListResponse,
    TweetResponse,
    TweetUpdate,
)


class TweetService:
    """Service for tweet operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tweet_repo = TweetRepository(db)
    
    async def create_tweet(
        self,
        tweet_data: TweetCreate,
        current_user: User,
    ) -> TweetResponse:
        """
        Create a new tweet.
        
        Args:
            tweet_data: Tweet creation data
            current_user: The user creating the tweet
            
        Returns:
            Created tweet response
        """
        # Validate quote tweet exists if provided
        quoted_tweet = None
        if tweet_data.quote_tweet_id:
            quoted_tweet_data = await self.tweet_repo.get_by_id(tweet_data.quote_tweet_id)
            if not quoted_tweet_data:
                raise NotFoundException("Quoted tweet not found")
            quoted_tweet = quoted_tweet_data
        
        # Create tweet
        tweet = Tweet(
            user_id=current_user.id,
            content=tweet_data.content,
            image_url=tweet_data.image_url,
            quote_tweet_id=tweet_data.quote_tweet_id,
        )
        
        tweet = await self.tweet_repo.create(tweet)
        
        # Build response
        return self._build_tweet_response(
            tweet=tweet,
            likes_count=0,
            comments_count=0,
            retweets_count=0,
            is_liked=False,
            is_retweeted=False,
            is_bookmarked=False,
            quoted_tweet=quoted_tweet,
        )
    
    async def get_tweet(
        self,
        tweet_id: uuid.UUID,
        current_user_id: uuid.UUID | None = None,
    ) -> TweetResponse:
        """
        Get a single tweet by ID.
        
        Args:
            tweet_id: UUID of the tweet
            current_user_id: Current user for interaction status
            
        Returns:
            Tweet response with counts and interaction status
        """
        data = await self.tweet_repo.get_with_counts(tweet_id, current_user_id)
        
        if not data:
            raise NotFoundException("Tweet not found")
        
        # Increment view count
        await self.tweet_repo.increment_views(tweet_id)
        
        return self._build_tweet_response(
            tweet=data["tweet"],
            likes_count=data["likes_count"],
            comments_count=data["comments_count"],
            retweets_count=data["retweets_count"],
            is_liked=data["is_liked"],
            is_retweeted=data["is_retweeted"],
            is_bookmarked=data["is_bookmarked"],
        )
    
    async def get_tweets(
        self,
        page: int = 1,
        limit: int = 20,
        user_id: uuid.UUID | None = None,
        current_user_id: uuid.UUID | None = None,
    ) -> TweetListResponse:
        """
        Get paginated list of tweets.
        
        Args:
            page: Page number (1-indexed)
            limit: Items per page
            user_id: Filter by user
            current_user_id: Current user for interaction status
            
        Returns:
            Paginated tweet list response
        """
        offset = (page - 1) * limit
        
        tweets_data, total_count = await self.tweet_repo.get_list(
            offset=offset,
            limit=limit,
            user_id=user_id,
            current_user_id=current_user_id,
        )
        
        tweets = [
            self._build_tweet_response(
                tweet=data["tweet"],
                likes_count=data["likes_count"],
                comments_count=data["comments_count"],
                retweets_count=data["retweets_count"],
                is_liked=data["is_liked"],
                is_retweeted=data["is_retweeted"],
                is_bookmarked=data["is_bookmarked"],
            )
            for data in tweets_data
        ]
        
        pagination = PaginationMeta.create(total_count, page, limit)
        
        return TweetListResponse(data=tweets, pagination=pagination)
    
    async def update_tweet(
        self,
        tweet_id: uuid.UUID,
        tweet_data: TweetUpdate,
        current_user: User,
    ) -> TweetResponse:
        """
        Update a tweet.
        
        Args:
            tweet_id: UUID of the tweet to update
            tweet_data: Update data
            current_user: The user making the update
            
        Returns:
            Updated tweet response
        """
        data = await self.tweet_repo.get_with_counts(tweet_id, current_user.id)
        
        if not data:
            raise NotFoundException("Tweet not found")
        
        tweet = data["tweet"]
        
        # Check ownership
        if tweet.user_id != current_user.id:
            raise ForbiddenException("You can only edit your own tweets")
        
        # Update fields
        if tweet_data.content is not None:
            tweet.content = tweet_data.content
        
        tweet = await self.tweet_repo.update(tweet)
        
        return self._build_tweet_response(
            tweet=tweet,
            likes_count=data["likes_count"],
            comments_count=data["comments_count"],
            retweets_count=data["retweets_count"],
            is_liked=data["is_liked"],
            is_retweeted=data["is_retweeted"],
            is_bookmarked=data["is_bookmarked"],
        )
    
    async def delete_tweet(
        self,
        tweet_id: uuid.UUID,
        current_user: User,
    ) -> None:
        """
        Delete a tweet.
        
        Args:
            tweet_id: UUID of the tweet to delete
            current_user: The user making the deletion
        """
        tweet = await self.tweet_repo.get_by_id(tweet_id)
        
        if not tweet:
            raise NotFoundException("Tweet not found")
        
        # Check ownership
        if tweet.user_id != current_user.id:
            raise ForbiddenException("You can only delete your own tweets")
        
        await self.tweet_repo.delete(tweet)
    
    def _build_tweet_response(
        self,
        tweet: Tweet,
        likes_count: int,
        comments_count: int,
        retweets_count: int,
        is_liked: bool,
        is_retweeted: bool,
        is_bookmarked: bool,
        quoted_tweet: Tweet | None = None,
    ) -> TweetResponse:
        """Build a TweetResponse from a Tweet model and counts."""
        # Use provided quoted_tweet or get from relationship
        qt = quoted_tweet or tweet.quoted_tweet
        quoted_tweet_response = None
        
        if qt:
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
            likes_count=likes_count,
            comments_count=comments_count,
            retweets_count=retweets_count,
            is_liked=is_liked,
            is_retweeted=is_retweeted,
            is_bookmarked=is_bookmarked,
        )
