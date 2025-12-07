"""
User Pydantic schemas for request/response validation.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    display_name: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=500)
    
    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Validate username contains only alphanumeric characters and underscores."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must contain only letters, numbers, and underscores")
        return v.lower()


class UserCreate(BaseModel):
    """Schema for creating a new user (registration)."""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    display_name: str | None = Field(None, max_length=100)
    
    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Validate username contains only alphanumeric characters and underscores."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must contain only letters, numbers, and underscores")
        return v.lower()
    
    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password has minimum requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    
    display_name: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=500)
    profile_image_url: str | None = Field(None, max_length=500)
    banner_image_url: str | None = Field(None, max_length=500)


class UserResponse(BaseModel):
    """Schema for user response (current user)."""
    
    id: uuid.UUID
    username: str
    email: EmailStr
    display_name: str | None
    bio: str | None
    profile_image_url: str | None
    banner_image_url: str | None
    is_verified: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    """Schema for public user profile (visible to other users)."""
    
    id: uuid.UUID
    username: str
    display_name: str | None
    bio: str | None
    profile_image_url: str | None
    banner_image_url: str | None
    created_at: datetime
    followers_count: int = 0
    following_count: int = 0
    is_following: bool = False  # Whether current user follows this user
    
    model_config = {"from_attributes": True}


class UserInDB(UserResponse):
    """Schema for user in database (includes password hash)."""
    
    password_hash: str
