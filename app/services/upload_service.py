"""
File upload service using Cloudinary.
"""

import re
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

from app.core.config import settings


def configure_cloudinary() -> None:
    """Configure Cloudinary with credentials from settings."""
    if not settings.cloudinary_url:
        raise ValueError("CLOUDINARY_URL not configured")
    
    # Parse Cloudinary URL: cloudinary://API_KEY:API_SECRET@CLOUD_NAME
    # The cloudinary library's cloudinary_url parameter doesn't always work,
    # so we parse it manually and configure explicitly
    match = re.match(r'cloudinary://([^:]+):([^@]+)@(.+)', settings.cloudinary_url)
    if not match:
        raise ValueError("Invalid CLOUDINARY_URL format. Expected: cloudinary://API_KEY:API_SECRET@CLOUD_NAME")
    
    api_key, api_secret, cloud_name = match.groups()
    
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True
    )



class FileUploadService:
    """Service for handling file uploads to Cloudinary."""
    
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self):
        configure_cloudinary()
    
    async def upload_profile_image(self, file: UploadFile, user_id: str) -> str:
        """
        Upload a profile image.
        
        Args:
            file: The uploaded file
            user_id: User ID for organizing uploads
            
        Returns:
            URL of the uploaded image
        """
        return await self._upload_image(
            file=file,
            folder=f"x_clone/profiles/{user_id}",
            transformation={
                "width": 400,
                "height": 400,
                "crop": "fill",
                "gravity": "face",
            }
        )
    
    async def upload_banner_image(self, file: UploadFile, user_id: str) -> str:
        """
        Upload a banner/cover image.
        
        Args:
            file: The uploaded file
            user_id: User ID for organizing uploads
            
        Returns:
            URL of the uploaded image
        """
        return await self._upload_image(
            file=file,
            folder=f"x_clone/banners/{user_id}",
            transformation={
                "width": 1500,
                "height": 500,
                "crop": "fill",
            }
        )
    
    async def upload_tweet_image(self, file: UploadFile, user_id: str) -> str:
        """
        Upload a tweet image.
        
        Args:
            file: The uploaded file
            user_id: User ID for organizing uploads
            
        Returns:
            URL of the uploaded image
        """
        return await self._upload_image(
            file=file,
            folder=f"x_clone/tweets/{user_id}",
            transformation={
                "width": 1200,
                "height": 675,
                "crop": "limit",  # Don't upscale, only downscale if larger
            }
        )
    
    async def _upload_image(
        self,
        file: UploadFile,
        folder: str,
        transformation: dict | None = None,
    ) -> str:
        """
        Internal method to upload an image to Cloudinary.
        
        Args:
            file: The uploaded file
            folder: Cloudinary folder path
            transformation: Optional image transformations
            
        Returns:
            URL of the uploaded image
            
        Raises:
            ValueError: If file type is not allowed or file is too large
        """
        # Validate file type
        if file.content_type not in self.ALLOWED_IMAGE_TYPES:
            raise ValueError(
                f"Invalid file type. Allowed: {', '.join(self.ALLOWED_IMAGE_TYPES)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size: {self.MAX_FILE_SIZE // 1024 // 1024}MB")
        
        # Upload to Cloudinary
        upload_options = {
            "folder": folder,
            "resource_type": "image",
        }
        
        if transformation:
            upload_options["transformation"] = transformation
        
        result = cloudinary.uploader.upload(content, **upload_options)
        
        return result["secure_url"]
    
    async def delete_image(self, public_id: str) -> bool:
        """
        Delete an image from Cloudinary.
        
        Args:
            public_id: Cloudinary public ID of the image
            
        Returns:
            True if deletion was successful
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get("result") == "ok"
        except Exception:
            return False


# Singleton instance
_upload_service: FileUploadService | None = None


def get_upload_service() -> FileUploadService:
    """Get or create the upload service singleton."""
    global _upload_service
    if _upload_service is None:
        _upload_service = FileUploadService()
    return _upload_service
