"""
User endpoints for profile management.
"""

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the profile of the currently authenticated user.",
)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> UserResponse:
    """
    Get the current user's profile.
    
    Requires authentication via Bearer token.
    """
    return UserResponse.model_validate(current_user)
