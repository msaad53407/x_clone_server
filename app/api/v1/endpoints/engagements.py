"""
Engagement endpoints for likes, retweets, and bookmarks.
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import MessageResponse
from app.schemas.tweet import TweetListResponse
from app.services.engagement_service import EngagementService

router = APIRouter(tags=["Engagement"])


# Like endpoints
@router.post(
    "/tweets/{tweet_id}/like",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Like a tweet",
    description="Like a tweet. Requires authentication.",
)
async def like_tweet(
    tweet_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> MessageResponse:
    """Like a tweet."""
    engagement_service = EngagementService(db)
    await engagement_service.like_tweet(tweet_id, current_user)
    return MessageResponse(message="Tweet liked")


@router.delete(
    "/tweets/{tweet_id}/like",
    response_model=MessageResponse,
    summary="Unlike a tweet",
    description="Remove like from a tweet.",
)
async def unlike_tweet(
    tweet_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> MessageResponse:
    """Unlike a tweet."""
    engagement_service = EngagementService(db)
    await engagement_service.unlike_tweet(tweet_id, current_user)
    return MessageResponse(message="Like removed")


# Retweet endpoints
@router.post(
    "/tweets/{tweet_id}/retweet",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Retweet",
    description="Retweet a tweet (simple retweet without comment).",
)
async def retweet(
    tweet_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> MessageResponse:
    """Retweet a tweet."""
    engagement_service = EngagementService(db)
    await engagement_service.retweet(tweet_id, current_user)
    return MessageResponse(message="Retweeted")


@router.delete(
    "/tweets/{tweet_id}/retweet",
    response_model=MessageResponse,
    summary="Undo retweet",
    description="Remove a retweet.",
)
async def unretweet(
    tweet_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> MessageResponse:
    """Undo a retweet."""
    engagement_service = EngagementService(db)
    await engagement_service.unretweet(tweet_id, current_user)
    return MessageResponse(message="Retweet removed")


# Bookmark endpoints
@router.post(
    "/tweets/{tweet_id}/bookmark",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bookmark a tweet",
    description="Save a tweet to bookmarks.",
)
async def bookmark_tweet(
    tweet_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> MessageResponse:
    """Bookmark a tweet."""
    engagement_service = EngagementService(db)
    await engagement_service.bookmark_tweet(tweet_id, current_user)
    return MessageResponse(message="Tweet bookmarked")


@router.delete(
    "/tweets/{tweet_id}/bookmark",
    response_model=MessageResponse,
    summary="Remove bookmark",
    description="Remove a tweet from bookmarks.",
)
async def unbookmark_tweet(
    tweet_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> MessageResponse:
    """Remove bookmark from a tweet."""
    engagement_service = EngagementService(db)
    await engagement_service.unbookmark_tweet(tweet_id, current_user)
    return MessageResponse(message="Bookmark removed")


@router.get(
    "/bookmarks",
    response_model=TweetListResponse,
    summary="Get bookmarks",
    description="Get all bookmarked tweets for the current user.",
)
async def get_bookmarks(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> TweetListResponse:
    """Get paginated list of bookmarked tweets."""
    engagement_service = EngagementService(db)
    return await engagement_service.get_bookmarks(current_user, page, limit)
