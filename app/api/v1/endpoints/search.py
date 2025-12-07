"""
Search endpoints for users and tweets.
"""

from typing import Any

from fastapi import APIRouter, Query

from app.api.deps import DbSession, OptionalUser
from app.schemas.common import PaginatedResponse
from app.schemas.tweet import TweetListResponse
from app.schemas.user import UserPublic
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


class UserSearchResponse(PaginatedResponse):
    """Paginated list of users from search."""
    
    data: list[UserPublic]


@router.get(
    "/users",
    response_model=UserSearchResponse,
    summary="Search users",
    description="Search for users by username or display name.",
)
async def search_users(
    db: DbSession,
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    current_user: OptionalUser = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> Any:
    """
    Search for users.
    
    Searches by username and display name (case-insensitive).
    """
    search_service = SearchService(db)
    result = await search_service.search_users(
        query=q,
        page=page,
        limit=limit,
        current_user_id=current_user.id if current_user else None,
    )
    return UserSearchResponse(data=result["data"], pagination=result["pagination"])


@router.get(
    "/tweets",
    response_model=TweetListResponse,
    summary="Search tweets",
    description="Search for tweets by content.",
)
async def search_tweets(
    db: DbSession,
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    current_user: OptionalUser = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> TweetListResponse:
    """
    Search for tweets.
    
    Searches tweet content (case-insensitive).
    """
    search_service = SearchService(db)
    return await search_service.search_tweets(
        query=q,
        page=page,
        limit=limit,
        current_user_id=current_user.id if current_user else None,
    )
