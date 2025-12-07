"""
Comment Pydantic schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.tweet import TweetAuthor


class CommentCreate(BaseModel):
    """Schema for creating a comment."""
    
    content: str = Field(..., min_length=1, max_length=280)


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""
    
    content: str = Field(..., min_length=1, max_length=280)


class CommentResponse(BaseModel):
    """Schema for comment response."""
    
    id: uuid.UUID
    content: str
    created_at: datetime
    updated_at: datetime
    author: TweetAuthor
    
    model_config = {"from_attributes": True}


class CommentListResponse(PaginatedResponse):
    """Paginated list of comments."""
    
    data: list[CommentResponse]
