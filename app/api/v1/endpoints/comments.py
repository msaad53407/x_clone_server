"""
Comment endpoints.
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.comment import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    CommentUpdate,
)
from app.schemas.common import MessageResponse
from app.services.comment_service import CommentService

router = APIRouter(tags=["Comments"])


@router.post(
    "/tweets/{tweet_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a comment",
    description="Add a comment to a tweet.",
)
async def create_comment(
    tweet_id: uuid.UUID,
    comment_data: CommentCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> CommentResponse:
    """
    Create a new comment on a tweet.
    
    - **content**: Comment text (1-280 characters)
    """
    comment_service = CommentService(db)
    return await comment_service.create_comment(tweet_id, comment_data, current_user)


@router.get(
    "/tweets/{tweet_id}/comments",
    response_model=CommentListResponse,
    summary="Get comments",
    description="Get paginated comments for a tweet.",
)
async def get_comments(
    tweet_id: uuid.UUID,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> CommentListResponse:
    """
    Get paginated comments for a tweet (newest first).
    """
    comment_service = CommentService(db)
    return await comment_service.get_comments(tweet_id, page, limit)


@router.patch(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    summary="Update a comment",
    description="Update a comment's content. Only the comment owner can update.",
)
async def update_comment(
    comment_id: uuid.UUID,
    comment_data: CommentUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> CommentResponse:
    """
    Update a comment's content.
    """
    comment_service = CommentService(db)
    return await comment_service.update_comment(comment_id, comment_data, current_user)


@router.delete(
    "/tweets/{tweet_id}/comments/{comment_id}",
    response_model=MessageResponse,
    summary="Delete a comment",
    description="Delete a comment. Comment owner or tweet owner can delete.",
)
async def delete_comment(
    tweet_id: uuid.UUID,
    comment_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> MessageResponse:
    """
    Delete a comment.
    
    Can be done by the comment owner or the tweet owner.
    """
    comment_service = CommentService(db)
    await comment_service.delete_comment(tweet_id, comment_id, current_user)
    return MessageResponse(message="Comment deleted successfully")
