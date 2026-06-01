"""
models/comment.py
-----------------
Comments support one level of threading (replies to comments).

Self-referencing relationship: A Comment can have a parent_id that points
to another Comment in the SAME table. This is how threaded comments work.

Rule: Replies cannot have replies (one level deep only).
This is enforced in the service layer, not at the DB level.
"""

from datetime import datetime
from sqlalchemy import Text, ForeignKey, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # parent_id is nullable - if NULL, this is a top-level comment.
    # If set, this is a reply to the comment with that ID.
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    article: Mapped["Article"] = relationship("Article", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")
    
    # Self-referencing: 'replies' loads child comments, 'parent' loads the parent comment
    replies: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    parent: Mapped["Comment | None"] = relationship(
        "Comment",
        back_populates="replies",
        remote_side=[id]  # 'remote_side' tells SQLAlchemy which side is the "one" in 1:N
    )
