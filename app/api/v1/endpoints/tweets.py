"""
Tweet endpoints for creating, reading, updating, and deleting tweets.
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession, OptionalUser
from app.schemas.common import MessageResponse
from app.schemas.tweet import (
    TweetCreate,
    TweetListResponse,
    TweetResponse,
    TweetUpdate,
)
from app.services.tweet_service import TweetService

router = APIRouter(prefix="/tweets", tags=["Tweets"])


@router.post(
    "",
    response_model=TweetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tweet",
    description="Create a new tweet. Can include text, image, and/or be a quote tweet.",
)
async def create_tweet(
    tweet_data: TweetCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> TweetResponse:
    """
    Create a new tweet.
    
    - **content**: Tweet text (max 280 characters)
    - **image_url**: Optional image URL
    - **quote_tweet_id**: Optional ID of tweet to quote
    
    At least one of content/image/quote_tweet_id is required.
    """
    tweet_service = TweetService(db)
    return await tweet_service.create_tweet(tweet_data, current_user)


@router.get(
    "",
    response_model=TweetListResponse,
    summary="Get all tweets",
    description="Get paginated list of all tweets (explore feed).",
)
async def get_tweets(
    db: DbSession,
    current_user: OptionalUser,
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> TweetListResponse:
    """
    Get paginated list of tweets (newest first).
    
    Returns engagement counts and current user's interaction status.
    """
    tweet_service = TweetService(db)
    return await tweet_service.get_tweets(
        page=page,
        limit=limit,
        current_user_id=current_user.id if current_user else None,
    )


@router.get(
    "/{tweet_id}",
    response_model=TweetResponse,
    summary="Get a tweet by ID",
    description="Get a single tweet by its ID.",
)
async def get_tweet(
    tweet_id: uuid.UUID,
    db: DbSession,
    current_user: OptionalUser,
) -> TweetResponse:
    """
    Get a single tweet by ID.
    
    Increments view count and returns engagement stats.
    """
    tweet_service = TweetService(db)
    return await tweet_service.get_tweet(
        tweet_id,
        current_user_id=current_user.id if current_user else None,
    )


@router.patch(
    "/{tweet_id}",
    response_model=TweetResponse,
    summary="Update a tweet",
    description="Update a tweet's content. Only the tweet owner can update.",
)
async def update_tweet(
    tweet_id: uuid.UUID,
    tweet_data: TweetUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> TweetResponse:
    """
    Update a tweet's content.
    
    Only the owner can update. Tweet will be marked as edited.
    """
    tweet_service = TweetService(db)
    return await tweet_service.update_tweet(tweet_id, tweet_data, current_user)


@router.delete(
    "/{tweet_id}",
    response_model=MessageResponse,
    summary="Delete a tweet",
    description="Delete a tweet. Only the tweet owner can delete.",
)
async def delete_tweet(
    tweet_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> MessageResponse:
    """
    Delete a tweet.
    
    Only the owner can delete. This also removes all associated
    likes, comments, and bookmarks.
    """
    tweet_service = TweetService(db)
    await tweet_service.delete_tweet(tweet_id, current_user)
    return MessageResponse(message="Tweet deleted successfully")
