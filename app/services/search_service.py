"""
Search service for searching users and tweets.
"""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.tweet import Tweet
from app.models.user import User
from app.repositories.follow_repository import FollowRepository
from app.repositories.tweet_repository import TweetRepository
from app.schemas.common import PaginationMeta
from app.schemas.tweet import (
    QuotedTweetResponse,
    TweetAuthor,
    TweetListResponse,
    TweetResponse,
)
from app.schemas.user import UserPublic


class UserSearchResponse:
    """Response for user search (for serialization)."""
    pass


class SearchService:
    """Service for search operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tweet_repo = TweetRepository(db)
        self.follow_repo = FollowRepository(db)
    
    async def search_users(
        self,
        query: str,
        page: int = 1,
        limit: int = 20,
        current_user_id: uuid.UUID | None = None,
    ) -> dict:
        """
        Search for users by username or display name.
        
        Args:
            query: Search query string
            page: Page number
            limit: Items per page
            current_user_id: Optional current user for follow status
            
        Returns:
            Dict with 'data' (list of UserPublic) and 'pagination'
        """
        offset = (page - 1) * limit
        search_term = f"%{query.lower()}%"
        
        # Count query
        count_query = (
            select(func.count(User.id))
            .where(
                or_(
                    User.username.ilike(search_term),
                    User.display_name.ilike(search_term),
                )
            )
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Data query
        data_query = (
            select(User)
            .where(
                or_(
                    User.username.ilike(search_term),
                    User.display_name.ilike(search_term),
                )
            )
            .order_by(User.username)
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.db.execute(data_query)
        users = result.scalars().all()
        
        # Build response
        users_response = []
        for user in users:
            followers_count = await self.follow_repo.get_followers_count(user.id)
            following_count = await self.follow_repo.get_following_count(user.id)
            is_following = False
            if current_user_id and current_user_id != user.id:
                is_following = await self.follow_repo.is_following(current_user_id, user.id)
            
            users_response.append(UserPublic(
                id=user.id,
                username=user.username,
                display_name=user.display_name,
                bio=user.bio,
                profile_image_url=user.profile_image_url,
                banner_image_url=user.banner_image_url,
                created_at=user.created_at,
                followers_count=followers_count,
                following_count=following_count,
                is_following=is_following,
            ))
        
        pagination = PaginationMeta.create(total_count, page, limit)
        
        return {"data": users_response, "pagination": pagination}
    
    async def search_tweets(
        self,
        query: str,
        page: int = 1,
        limit: int = 20,
        current_user_id: uuid.UUID | None = None,
    ) -> TweetListResponse:
        """
        Search for tweets by content.
        
        Args:
            query: Search query string
            page: Page number
            limit: Items per page
            current_user_id: Optional current user for engagement status
            
        Returns:
            Paginated tweet list
        """
        offset = (page - 1) * limit
        search_term = f"%{query.lower()}%"
        
        # Count query
        count_query = (
            select(func.count(Tweet.id))
            .where(Tweet.content.ilike(search_term))
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Data query
        data_query = (
            select(Tweet)
            .options(
                joinedload(Tweet.user),
                joinedload(Tweet.quoted_tweet).joinedload(Tweet.user),
            )
            .where(Tweet.content.ilike(search_term))
            .order_by(Tweet.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.db.execute(data_query)
        tweets = result.unique().scalars().all()
        
        # Build responses with counts
        tweets_response = []
        for tweet in tweets:
            data = await self.tweet_repo.get_with_counts(tweet.id, current_user_id)
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
