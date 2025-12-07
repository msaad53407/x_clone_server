"""
Feed endpoints for home feed and explore.
"""

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession, OptionalUser
from app.schemas.tweet import TweetListResponse
from app.services.feed_service import FeedService

router = APIRouter(prefix="/feed", tags=["Feed"])


@router.get(
    "/home",
    response_model=TweetListResponse,
    summary="Get home feed",
    description="Get personalized home feed with tweets from followed users and recommendations.",
)
async def get_home_feed(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> TweetListResponse:
    """
    Get personalized home feed.
    
    Uses collaborative filtering to recommend tweets based on user's
    interactions (likes, comments, bookmarks) combined with
    tweets from followed users.
    """
    feed_service = FeedService(db)
    return await feed_service.get_home_feed(
        current_user_id=current_user.id,
        page=page,
        limit=limit,
    )


@router.get(
    "/explore",
    response_model=TweetListResponse,
    summary="Get explore feed",
    description="Get explore feed showing recent tweets from all users.",
)
async def get_explore_feed(
    db: DbSession,
    current_user: OptionalUser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> TweetListResponse:
    """
    Get explore feed with recent tweets.
    
    Shows recent tweets from all users, sorted by creation time.
    """
    feed_service = FeedService(db)
    return await feed_service.get_explore_feed_simple(
        page=page,
        limit=limit,
        current_user_id=current_user.id if current_user else None,
    )
