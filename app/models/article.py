"""
models/article.py
-----------------
The Article model and the article_tags association table.

Many-to-many relationship: An article can have many tags, and a tag can
belong to many articles. In SQL, this requires a "join table" (article_tags)
that stores pairs of article_id and tag_id.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    String, Text, Boolean, Integer, ForeignKey, DateTime, Table, Column, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ArticleStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


# Association table for the many-to-many relationship between Article and Tag.
# This is just a plain table (not a full model class) since it only stores IDs.
article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Article(Base):
    """
    Represents the 'articles' table.
    
    Key design decisions:
    - Soft delete: articles are ARCHIVED, never truly deleted from DB
    - Slug is auto-generated from title (handled in the service layer)
    - view_count is incremented every time an article is fetched
    """
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(350), unique=True, index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(280), nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[ArticleStatus] = mapped_column(
        String(20),
        default=ArticleStatus.DRAFT,
        nullable=False
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    author: Mapped["User"] = relationship("User", back_populates="articles")
    
    # secondary=article_tags tells SQLAlchemy to use the join table automatically
    tags: Mapped[list["Tag"]] = relationship(
        "Tag", secondary=article_tags, back_populates="articles"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="article", cascade="all, delete-orphan"
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        "Bookmark", back_populates="article", cascade="all, delete-orphan"
    )
