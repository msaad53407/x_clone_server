"""
Tweet model for storing posts/tweets.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Tweet(Base):
    """Tweet/Post model."""
    
    __tablename__ = "tweets"
    
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
    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    quote_tweet_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tweets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    views_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_edited: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="tweets",
    )
    quoted_tweet: Mapped["Tweet | None"] = relationship(
        "Tweet",
        remote_side=[id],
        foreign_keys=[quote_tweet_id],
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="tweet",
        cascade="all, delete-orphan",
    )
    likes: Mapped[list["Like"]] = relationship(
        "Like",
        back_populates="tweet",
        cascade="all, delete-orphan",
    )
    retweets: Mapped[list["Retweet"]] = relationship(
        "Retweet",
        back_populates="tweet",
        cascade="all, delete-orphan",
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        "Bookmark",
        back_populates="tweet",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Tweet(id={self.id}, user_id={self.user_id})>"


# Import for type hints
from app.models.user import User  # noqa: E402
from app.models.comment import Comment  # noqa: E402
from app.models.like import Like  # noqa: E402
from app.models.retweet import Retweet  # noqa: E402
from app.models.bookmark import Bookmark  # noqa: E402
