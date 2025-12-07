"""
User model for storing user account information.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """User account model."""
    
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    profile_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    banner_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Relationships
    tweets: Mapped[list["Tweet"]] = relationship(
        "Tweet",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    likes: Mapped[list["Like"]] = relationship(
        "Like",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    retweets: Mapped[list["Retweet"]] = relationship(
        "Retweet",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        "Bookmark",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    # Follow relationships
    followers: Mapped[list["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.following_id",
        back_populates="following",
        cascade="all, delete-orphan",
    )
    following: Mapped[list["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


# Import for type hints (avoid circular imports)
from app.models.tweet import Tweet  # noqa: E402
from app.models.comment import Comment  # noqa: E402
from app.models.like import Like  # noqa: E402
from app.models.follow import Follow  # noqa: E402
from app.models.retweet import Retweet  # noqa: E402
from app.models.bookmark import Bookmark  # noqa: E402
