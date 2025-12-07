"""
Bookmark model for storing saved/bookmarked tweets.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Bookmark(Base):
    """Bookmark (saved tweet) model."""
    
    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "tweet_id", name="uq_bookmarks_user_tweet"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tweet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tweets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="bookmarks",
    )
    tweet: Mapped["Tweet"] = relationship(
        "Tweet",
        back_populates="bookmarks",
    )
    
    def __repr__(self) -> str:
        return f"<Bookmark(id={self.id}, user_id={self.user_id}, tweet_id={self.tweet_id})>"


# Import for type hints
from app.models.user import User  # noqa: E402
from app.models.tweet import Tweet  # noqa: E402
