"""
File upload endpoints.
"""

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import BadRequestException
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse
from app.services.upload_service import get_upload_service

router = APIRouter(prefix="/upload", tags=["Upload"])


class UploadResponse:
    """Response with uploaded file URL."""
    url: str


@router.post(
    "/profile-image",
    response_model=UserResponse,
    summary="Upload profile image",
    description="Upload and set profile image for current user.",
)
async def upload_profile_image(
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> UserResponse:
    """
    Upload a profile image.
    
    - Max size: 10MB
    - Allowed formats: JPEG, PNG, GIF, WebP
    - Image will be cropped to 400x400 pixels
    """
    try:
        upload_service = get_upload_service()
        url = await upload_service.upload_profile_image(file, str(current_user.id))
        
        # Update user profile
        current_user.profile_image_url = url
        user_repo = UserRepository(db)
        current_user = await user_repo.update(current_user)
        
        return UserResponse.model_validate(current_user)
    except ValueError as e:
        raise BadRequestException(str(e))


@router.post(
    "/banner-image",
    response_model=UserResponse,
    summary="Upload banner image",
    description="Upload and set banner/cover image for current user.",
)
async def upload_banner_image(
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> UserResponse:
    """
    Upload a banner/cover image.
    
    - Max size: 10MB
    - Allowed formats: JPEG, PNG, GIF, WebP
    - Image will be cropped to 1500x500 pixels
    """
    try:
        upload_service = get_upload_service()
        url = await upload_service.upload_banner_image(file, str(current_user.id))
        
        # Update user profile
        current_user.banner_image_url = url
        user_repo = UserRepository(db)
        current_user = await user_repo.update(current_user)
        
        return UserResponse.model_validate(current_user)
    except ValueError as e:
        raise BadRequestException(str(e))


@router.post(
    "/tweet-image",
    summary="Upload tweet image",
    description="Upload an image for use in a tweet.",
)
async def upload_tweet_image(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> dict:
    """
    Upload an image for a tweet.
    
    - Max size: 10MB
    - Allowed formats: JPEG, PNG, GIF, WebP
    - Returns the image URL to use when creating a tweet
    """
    try:
        upload_service = get_upload_service()
        url = await upload_service.upload_tweet_image(file, str(current_user.id))
        
        return {"url": url, "success": True}
    except ValueError as e:
        raise BadRequestException(str(e))
