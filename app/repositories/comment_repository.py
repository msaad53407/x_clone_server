"""
Comment repository for database operations.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.comment import Comment


class CommentRepository:
    """Repository for comment database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, comment: Comment) -> Comment:
        """Create a new comment."""
        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment)
        # Load the user relationship
        result = await self.db.execute(
            select(Comment)
            .options(joinedload(Comment.user))
            .where(Comment.id == comment.id)
        )
        return result.unique().scalar_one()
    
    async def get_by_id(self, comment_id: uuid.UUID) -> Comment | None:
        """Get a comment by ID."""
        result = await self.db.execute(
            select(Comment)
            .options(joinedload(Comment.user))
            .where(Comment.id == comment_id)
        )
        return result.unique().scalar_one_or_none()
    
    async def get_by_tweet(
        self,
        tweet_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Comment], int]:
        """Get paginated comments for a tweet."""
        # Count query
        count_result = await self.db.execute(
            select(func.count(Comment.id)).where(Comment.tweet_id == tweet_id)
        )
        total_count = count_result.scalar() or 0
        
        # Data query
        result = await self.db.execute(
            select(Comment)
            .options(joinedload(Comment.user))
            .where(Comment.tweet_id == tweet_id)
            .order_by(Comment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        comments = result.unique().scalars().all()
        
        return list(comments), total_count
    
    async def update(self, comment: Comment) -> Comment:
        """Update a comment."""
        await self.db.flush()
        await self.db.refresh(comment)
        return comment
    
    async def delete(self, comment: Comment) -> None:
        """Delete a comment."""
        await self.db.delete(comment)
        await self.db.flush()
