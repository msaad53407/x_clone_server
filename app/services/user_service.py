"""
User service for profile and follow operations.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.user import User
from app.repositories.follow_repository import FollowRepository
from app.repositories.tweet_repository import TweetRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginationMeta
from app.schemas.tweet import TweetListResponse, TweetResponse, TweetAuthor, QuotedTweetResponse
from app.schemas.user import UserPublic, UserResponse, UserUpdate


class UserListResponse(PaginationMeta):
    """Response type for user list (defined here to avoid circular imports)."""
    pass


class UserService:
    """Service for user operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.follow_repo = FollowRepository(db)
        self.tweet_repo = TweetRepository(db)
    
    async def get_user_by_username(
        self,
        username: str,
        current_user_id: uuid.UUID | None = None,
    ) -> UserPublic:
        """Get a user's public profile by username."""
        user = await self.user_repo.get_by_username(username)
        
        if not user:
            raise NotFoundException("User not found")
        
        followers_count = await self.follow_repo.get_followers_count(user.id)
        following_count = await self.follow_repo.get_following_count(user.id)
        
        is_following = False
        if current_user_id:
            is_following = await self.follow_repo.is_following(current_user_id, user.id)
        
        return UserPublic(
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
        )
    
    async def get_user_tweets(
        self,
        username: str,
        page: int = 1,
        limit: int = 20,
        current_user_id: uuid.UUID | None = None,
    ) -> TweetListResponse:
        """Get tweets by a specific user."""
        user = await self.user_repo.get_by_username(username)
        
        if not user:
            raise NotFoundException("User not found")
        
        offset = (page - 1) * limit
        
        tweets_data, total_count = await self.tweet_repo.get_list(
            offset=offset,
            limit=limit,
            user_id=user.id,
            current_user_id=current_user_id,
        )
        
        tweets = [
            self._build_tweet_response(data)
            for data in tweets_data
        ]
        
        pagination = PaginationMeta.create(total_count, page, limit)
        
        return TweetListResponse(data=tweets, pagination=pagination)
    
    async def update_profile(
        self,
        current_user: User,
        update_data: UserUpdate,
    ) -> UserResponse:
        """Update the current user's profile."""
        if update_data.display_name is not None:
            current_user.display_name = update_data.display_name
        if update_data.bio is not None:
            current_user.bio = update_data.bio
        if update_data.profile_image_url is not None:
            current_user.profile_image_url = update_data.profile_image_url
        if update_data.banner_image_url is not None:
            current_user.banner_image_url = update_data.banner_image_url
        
        current_user = await self.user_repo.update(current_user)
        
        return UserResponse.model_validate(current_user)
    
    async def follow_user(
        self,
        username: str,
        current_user: User,
    ) -> None:
        """Follow a user."""
        user_to_follow = await self.user_repo.get_by_username(username)
        
        if not user_to_follow:
            raise NotFoundException("User not found")
        
        if user_to_follow.id == current_user.id:
            raise BadRequestException("Cannot follow yourself")
        
        # Check if already following
        existing = await self.follow_repo.get_follow(current_user.id, user_to_follow.id)
        if existing:
            raise BadRequestException("Already following this user")
        
        await self.follow_repo.create_follow(current_user.id, user_to_follow.id)
    
    async def unfollow_user(
        self,
        username: str,
        current_user: User,
    ) -> None:
        """Unfollow a user."""
        user_to_unfollow = await self.user_repo.get_by_username(username)
        
        if not user_to_unfollow:
            raise NotFoundException("User not found")
        
        follow = await self.follow_repo.get_follow(current_user.id, user_to_unfollow.id)
        if not follow:
            raise NotFoundException("Not following this user")
        
        await self.follow_repo.delete_follow(follow)
    
    async def get_followers(
        self,
        username: str,
        page: int = 1,
        limit: int = 20,
        current_user_id: uuid.UUID | None = None,
    ) -> dict:
        """Get paginated list of followers."""
        user = await self.user_repo.get_by_username(username)
        
        if not user:
            raise NotFoundException("User not found")
        
        offset = (page - 1) * limit
        followers, total_count = await self.follow_repo.get_followers(user.id, offset, limit)
        
        # Build response
        users_response = []
        for follower in followers:
            followers_count = await self.follow_repo.get_followers_count(follower.id)
            following_count = await self.follow_repo.get_following_count(follower.id)
            is_following = False
            if current_user_id:
                is_following = await self.follow_repo.is_following(current_user_id, follower.id)
            
            users_response.append(UserPublic(
                id=follower.id,
                username=follower.username,
                display_name=follower.display_name,
                bio=follower.bio,
                profile_image_url=follower.profile_image_url,
                banner_image_url=follower.banner_image_url,
                created_at=follower.created_at,
                followers_count=followers_count,
                following_count=following_count,
                is_following=is_following,
            ))
        
        pagination = PaginationMeta.create(total_count, page, limit)
        
        return {"data": users_response, "pagination": pagination}
    
    async def get_following(
        self,
        username: str,
        page: int = 1,
        limit: int = 20,
        current_user_id: uuid.UUID | None = None,
    ) -> dict:
        """Get paginated list of users being followed."""
        user = await self.user_repo.get_by_username(username)
        
        if not user:
            raise NotFoundException("User not found")
        
        offset = (page - 1) * limit
        following_users, total_count = await self.follow_repo.get_following(user.id, offset, limit)
        
        # Build response
        users_response = []
        for following_user in following_users:
            followers_count = await self.follow_repo.get_followers_count(following_user.id)
            following_count = await self.follow_repo.get_following_count(following_user.id)
            is_following = False
            if current_user_id:
                is_following = await self.follow_repo.is_following(current_user_id, following_user.id)
            
            users_response.append(UserPublic(
                id=following_user.id,
                username=following_user.username,
                display_name=following_user.display_name,
                bio=following_user.bio,
                profile_image_url=following_user.profile_image_url,
                banner_image_url=following_user.banner_image_url,
                created_at=following_user.created_at,
                followers_count=followers_count,
                following_count=following_count,
                is_following=is_following,
            ))
        
        pagination = PaginationMeta.create(total_count, page, limit)
        
        return {"data": users_response, "pagination": pagination}
    
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
