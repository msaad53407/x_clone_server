"""
Tweet Pydantic schemas for request/response validation.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.user import UserPublic


class TweetBase(BaseModel):
    """Base tweet schema."""
    
    content: str | None = Field(None, max_length=280)
    image_url: str | None = Field(None, max_length=500)


class TweetCreate(BaseModel):
    """Schema for creating a new tweet."""
    
    content: str | None = Field(None, max_length=280)
    image_url: str | None = Field(None, max_length=500)
    quote_tweet_id: uuid.UUID | None = None
    
    def model_post_init(self, __context):
        """Validate that tweet has at least content or image."""
        if not self.content and not self.image_url and not self.quote_tweet_id:
            raise ValueError("Tweet must have content, image, or be a quote tweet")


class TweetUpdate(BaseModel):
    """Schema for updating a tweet."""
    
    content: str | None = Field(None, max_length=280)


class TweetAuthor(BaseModel):
    """Minimal author info for tweet responses."""
    
    id: uuid.UUID
    username: str
    display_name: str | None
    profile_image_url: str | None
    
    model_config = {"from_attributes": True}


class QuotedTweetResponse(BaseModel):
    """Schema for quoted tweet (nested in tweet response)."""
    
    id: uuid.UUID
    content: str | None
    image_url: str | None
    created_at: datetime
    author: TweetAuthor
    
    model_config = {"from_attributes": True}


class TweetResponse(BaseModel):
    """Schema for tweet response."""
    
    id: uuid.UUID
    content: str | None
    image_url: str | None
    views_count: int
    is_edited: bool
    created_at: datetime
    updated_at: datetime
    author: TweetAuthor
    quoted_tweet: QuotedTweetResponse | None = None
    
    # Engagement counts
    likes_count: int = 0
    comments_count: int = 0
    retweets_count: int = 0
    
    # Current user interaction status
    is_liked: bool = False
    is_retweeted: bool = False
    is_bookmarked: bool = False
    
    model_config = {"from_attributes": True}


class TweetListResponse(PaginatedResponse):
    """Paginated list of tweets."""
    
    data: list[TweetResponse]


class TweetDetailResponse(BaseModel):
    """Single tweet detail response."""
    
    data: TweetResponse
