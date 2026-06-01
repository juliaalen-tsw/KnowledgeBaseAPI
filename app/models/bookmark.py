"""
models/bookmark.py
------------------
A bookmark is a user saving an article for later.

Key constraint: UniqueConstraint ensures a user can only bookmark
an article ONCE. The database will reject duplicate attempts.
"""

from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Bookmark(Base):
    __tablename__ = "bookmarks"

    # Composite unique constraint: the combination of user_id + article_id must be unique
    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="uq_user_article_bookmark"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="bookmarks")
    article: Mapped["Article"] = relationship("Article", back_populates="bookmarks")
