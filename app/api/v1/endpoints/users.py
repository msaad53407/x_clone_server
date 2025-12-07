"""
User endpoints for profile management and follow operations.
"""

from typing import Any

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession, OptionalUser
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationMeta
from app.schemas.tweet import TweetListResponse
from app.schemas.user import UserPublic, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


class UserListResponse(PaginatedResponse):
    """Paginated list of users."""
    
    data: list[UserPublic]


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the profile of the currently authenticated user.",
)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> UserResponse:
    """Get the current user's profile."""
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update the current user's profile information.",
)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> UserResponse:
    """
    Update the current user's profile.
    
    - **display_name**: Display name
    - **bio**: User bio
    - **profile_image_url**: Profile image URL
    - **banner_image_url**: Banner image URL
    """
    user_service = UserService(db)
    return await user_service.update_profile(current_user, update_data)


@router.get(
    "/{username}",
    response_model=UserPublic,
    summary="Get user by username",
    description="Get a user's public profile by username.",
)
async def get_user_by_username(
    username: str,
    db: DbSession,
    current_user: OptionalUser,
) -> UserPublic:
    """
    Get a user's public profile.
    
    Includes follower/following counts and whether current user follows them.
    """
    user_service = UserService(db)
    return await user_service.get_user_by_username(
        username,
        current_user_id=current_user.id if current_user else None,
    )


@router.get(
    "/{username}/tweets",
    response_model=TweetListResponse,
    summary="Get user's tweets",
    description="Get paginated list of tweets by a specific user.",
)
async def get_user_tweets(
    username: str,
    db: DbSession,
    current_user: OptionalUser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> TweetListResponse:
    """Get a user's tweets."""
    user_service = UserService(db)
    return await user_service.get_user_tweets(
        username,
        page=page,
        limit=limit,
        current_user_id=current_user.id if current_user else None,
    )


@router.post(
    "/{username}/follow",
    response_model=MessageResponse,
    summary="Follow a user",
    description="Follow a user by their username.",
)
async def follow_user(
    username: str,
    current_user: CurrentUser,
    db: DbSession,
) -> MessageResponse:
    """Follow a user."""
    user_service = UserService(db)
    await user_service.follow_user(username, current_user)
    return MessageResponse(message=f"You are now following @{username}")


@router.delete(
    "/{username}/follow",
    response_model=MessageResponse,
    summary="Unfollow a user",
    description="Unfollow a user by their username.",
)
async def unfollow_user(
    username: str,
    current_user: CurrentUser,
    db: DbSession,
) -> MessageResponse:
    """Unfollow a user."""
    user_service = UserService(db)
    await user_service.unfollow_user(username, current_user)
    return MessageResponse(message=f"You have unfollowed @{username}")


@router.get(
    "/{username}/followers",
    response_model=UserListResponse,
    summary="Get user's followers",
    description="Get paginated list of followers for a user.",
)
async def get_followers(
    username: str,
    db: DbSession,
    current_user: OptionalUser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> Any:
    """Get a user's followers."""
    user_service = UserService(db)
    result = await user_service.get_followers(
        username,
        page=page,
        limit=limit,
        current_user_id=current_user.id if current_user else None,
    )
    return UserListResponse(data=result["data"], pagination=result["pagination"])


@router.get(
    "/{username}/following",
    response_model=UserListResponse,
    summary="Get user's following",
    description="Get paginated list of users that a user is following.",
)
async def get_following(
    username: str,
    db: DbSession,
    current_user: OptionalUser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> Any:
    """Get users that this user is following."""
    user_service = UserService(db)
    result = await user_service.get_following(
        username,
        page=page,
        limit=limit,
        current_user_id=current_user.id if current_user else None,
    )
    return UserListResponse(data=result["data"], pagination=result["pagination"])


@router.get(
    "/suggestions/who-to-follow",
    response_model=list[UserPublic],
    summary="Get user suggestions",
    description="Get users the current user might want to follow.",
)
async def get_user_suggestions(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=3, ge=1, le=10),
) -> list[UserPublic]:
    """
    Get user suggestions for "Who to follow".
    
    Returns users that the current user is not following.
    If there are no such users, returns random users.
    """
    user_service = UserService(db)
    return await user_service.get_suggestions(current_user.id, limit)

