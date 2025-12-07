"""
Feed service for personalized home feed and explore feed.
"""

import uuid

from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.follow import Follow
from app.models.tweet import Tweet
from app.models.user import User
from app.repositories.tweet_repository import TweetRepository
from app.schemas.common import PaginationMeta
from app.schemas.tweet import (
    QuotedTweetResponse,
    TweetAuthor,
    TweetListResponse,
    TweetResponse,
)
from app.services.recommender_service import get_recommender, refresh_recommender


class FeedService:
    """Service for generating personalized feeds."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tweet_repo = TweetRepository(db)
    
    async def get_home_feed(
        self,
        current_user_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
    ) -> TweetListResponse:
        """
        Get personalized home feed for a user.
        
        Algorithm:
        1. Get recommended tweets from collaborative filtering
        2. Get tweets from followed users
        3. Merge and deduplicate, prioritizing recommendations
        4. Fall back to recent tweets if not enough content
        
        Args:
            current_user_id: Current user UUID
            page: Page number
            limit: Items per page
            
        Returns:
            Paginated tweet list
        """
        offset = (page - 1) * limit
        
        # Try to refresh recommender (will use cached if still valid)
        try:
            await refresh_recommender(self.db)
        except Exception:
            pass  # Continue without recommendations if it fails
        
        # Get recommendations
        recommender = get_recommender()
        recommended_ids = recommender.get_recommendations(
            current_user_id,
            n_recommendations=limit * 3,
            filter_interacted=True,
        )
        
        # Get tweets from followed users
        following_subquery = (
            select(Follow.following_id)
            .where(Follow.follower_id == current_user_id)
        )
        
        # Build feed query
        if recommended_ids:
            # Combine recommended + followed users' tweets
            query = (
                select(Tweet)
                .options(
                    joinedload(Tweet.user),
                    joinedload(Tweet.quoted_tweet).joinedload(Tweet.user),
                )
                .where(
                    or_(
                        Tweet.id.in_(recommended_ids),
                        Tweet.user_id.in_(following_subquery),
                        Tweet.user_id == current_user_id,  # Include own tweets
                    )
                )
                .order_by(Tweet.created_at.desc())
            )
        else:
            # Fall back to followed users + own tweets
            query = (
                select(Tweet)
                .options(
                    joinedload(Tweet.user),
                    joinedload(Tweet.quoted_tweet).joinedload(Tweet.user),
                )
                .where(
                    or_(
                        Tweet.user_id.in_(following_subquery),
                        Tweet.user_id == current_user_id,
                    )
                )
                .order_by(Tweet.created_at.desc())
            )
        
        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        tweets = result.unique().scalars().all()
        
        # If still not enough tweets, get recent public tweets
        if len(tweets) < limit and page == 1:
            existing_ids = [t.id for t in tweets]
            additional_query = (
                select(Tweet)
                .options(
                    joinedload(Tweet.user),
                    joinedload(Tweet.quoted_tweet).joinedload(Tweet.user),
                )
                .where(Tweet.id.not_in(existing_ids) if existing_ids else True)
                .order_by(Tweet.created_at.desc())
                .limit(limit - len(tweets))
            )
            additional_result = await self.db.execute(additional_query)
            additional_tweets = additional_result.unique().scalars().all()
            tweets = list(tweets) + list(additional_tweets)
            total_count = max(total_count, len(tweets))
        
        # Build responses with counts
        tweets_response = []
        for tweet in tweets:
            data = await self.tweet_repo.get_with_counts(tweet.id, current_user_id)
            if data:
                tweets_response.append(self._build_tweet_response(data))
        
        pagination = PaginationMeta.create(total_count, page, limit)
        
        return TweetListResponse(data=tweets_response, pagination=pagination)
    
    async def get_explore_feed(
        self,
        page: int = 1,
        limit: int = 20,
        current_user_id: uuid.UUID | None = None,
    ) -> TweetListResponse:
        """
        Get explore feed showing trending/popular tweets.
        
        Algorithm: Sort by engagement (likes + comments) and recency.
        
        Args:
            page: Page number
            limit: Items per page
            current_user_id: Optional current user for engagement status
            
        Returns:
            Paginated tweet list
        """
        # This is essentially all tweets sorted by recency
        # In a production app, you'd add engagement scoring
        return await self.tweet_repo.get_list(
            offset=(page - 1) * limit,
            limit=limit,
            current_user_id=current_user_id,
        ).then(lambda result: self._format_list_response(result, page, limit))
    
    async def get_explore_feed_simple(
        self,
        page: int = 1,
        limit: int = 20,
        current_user_id: uuid.UUID | None = None,
    ) -> TweetListResponse:
        """
        Get explore feed - simpler implementation using tweet repo.
        """
        offset = (page - 1) * limit
        
        tweets_data, total_count = await self.tweet_repo.get_list(
            offset=offset,
            limit=limit,
            current_user_id=current_user_id,
        )
        
        tweets = [
            self._build_tweet_response(data)
            for data in tweets_data
        ]
        
        pagination = PaginationMeta.create(total_count, page, limit)
        
        return TweetListResponse(data=tweets, pagination=pagination)
    
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
            is_liked=data["is_liked"],
            is_bookmarked=data["is_bookmarked"],
        )
