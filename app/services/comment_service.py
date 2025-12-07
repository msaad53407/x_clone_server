"""
Comment service for business logic.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.comment import Comment
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.tweet_repository import TweetRepository
from app.schemas.comment import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    CommentUpdate,
)
from app.schemas.common import PaginationMeta
from app.schemas.tweet import TweetAuthor


class CommentService:
    """Service for comment operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.comment_repo = CommentRepository(db)
        self.tweet_repo = TweetRepository(db)
    
    async def create_comment(
        self,
        tweet_id: uuid.UUID,
        comment_data: CommentCreate,
        current_user: User,
    ) -> CommentResponse:
        """Create a new comment on a tweet."""
        # Verify tweet exists
        tweet = await self.tweet_repo.get_by_id(tweet_id)
        if not tweet:
            raise NotFoundException("Tweet not found")
        
        # Create comment
        comment = Comment(
            user_id=current_user.id,
            tweet_id=tweet_id,
            content=comment_data.content,
        )
        
        comment = await self.comment_repo.create(comment)
        
        return self._build_comment_response(comment)
    
    async def get_comments(
        self,
        tweet_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
    ) -> CommentListResponse:
        """Get paginated comments for a tweet."""
        # Verify tweet exists
        tweet = await self.tweet_repo.get_by_id(tweet_id)
        if not tweet:
            raise NotFoundException("Tweet not found")
        
        offset = (page - 1) * limit
        comments, total_count = await self.comment_repo.get_by_tweet(
            tweet_id, offset, limit
        )
        
        comments_response = [
            self._build_comment_response(comment)
            for comment in comments
        ]
        
        pagination = PaginationMeta.create(total_count, page, limit)
        
        return CommentListResponse(data=comments_response, pagination=pagination)
    
    async def update_comment(
        self,
        comment_id: uuid.UUID,
        comment_data: CommentUpdate,
        current_user: User,
    ) -> CommentResponse:
        """Update a comment."""
        comment = await self.comment_repo.get_by_id(comment_id)
        
        if not comment:
            raise NotFoundException("Comment not found")
        
        # Check ownership
        if comment.user_id != current_user.id:
            raise ForbiddenException("You can only edit your own comments")
        
        comment.content = comment_data.content
        comment.updated_at = datetime.now(timezone.utc)
        
        comment = await self.comment_repo.update(comment)
        
        return self._build_comment_response(comment)
    
    async def delete_comment(
        self,
        tweet_id: uuid.UUID,
        comment_id: uuid.UUID,
        current_user: User,
    ) -> None:
        """Delete a comment."""
        comment = await self.comment_repo.get_by_id(comment_id)
        
        if not comment:
            raise NotFoundException("Comment not found")
        
        # Get tweet to check if current user is tweet owner
        tweet = await self.tweet_repo.get_by_id(tweet_id)
        if not tweet:
            raise NotFoundException("Tweet not found")
        
        # Check if user is comment owner or tweet owner
        is_comment_owner = comment.user_id == current_user.id
        is_tweet_owner = tweet.user_id == current_user.id
        
        if not is_comment_owner and not is_tweet_owner:
            raise ForbiddenException("You can only delete your own comments or comments on your tweets")
        
        await self.comment_repo.delete(comment)
    
    def _build_comment_response(self, comment: Comment) -> CommentResponse:
        """Build a CommentResponse from a Comment model."""
        return CommentResponse(
            id=comment.id,
            content=comment.content,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            author=TweetAuthor(
                id=comment.user.id,
                username=comment.user.username,
                display_name=comment.user.display_name,
                profile_image_url=comment.user.profile_image_url,
            ),
        )
