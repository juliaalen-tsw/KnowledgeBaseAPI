"""
services/comment_service.py
----------------------------
Business logic for comments.

Threading rules:
- A comment can reply to another comment (parent_id set)
- But replies cannot have replies (one level deep only)
- Only author or admin can delete a comment
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.comment import Comment
from app.models.article import Article, ArticleStatus
from app.models.user import User, UserRole
from app.schemas.comment import CommentCreate


async def get_article_comments(slug: str, db: AsyncSession) -> list[Comment]:
    """
    Get all TOP-LEVEL comments for an article, with their replies nested.
    Only returns parent_id=None comments (top-level).
    Replies are loaded via the 'replies' relationship.
    """
    # First, verify the article exists and is published
    art_result = await db.execute(
        select(Article)
        .where(Article.slug == slug)
        .where(Article.status == ArticleStatus.PUBLISHED)
    )
    article = art_result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    result = await db.execute(
        select(Comment)
        .options(
            selectinload(Comment.author),
            selectinload(Comment.replies).selectinload(Comment.author),
        )
        .where(Comment.article_id == article.id)
        .where(Comment.parent_id.is_(None))  # Only top-level comments
        .order_by(Comment.created_at.asc())
    )
    return list(result.scalars().unique().all())


async def create_comment(
    slug: str,
    data: CommentCreate,
    author: User,
    db: AsyncSession,
) -> Comment:
    """
    Add a comment to an article.
    
    If parent_id is provided, this is a reply.
    Validate that the parent is a top-level comment (prevent nesting > 1 level).
    """
    art_result = await db.execute(
        select(Article)
        .where(Article.slug == slug)
        .where(Article.status == ArticleStatus.PUBLISHED)
    )
    article = art_result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Validate parent comment if this is a reply
    if data.parent_id is not None:
        parent_result = await db.execute(
            select(Comment).where(Comment.id == data.parent_id)
        )
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        # Prevent replies to replies (one level deep only)
        if parent.parent_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Cannot reply to a reply. Only one level of nesting is allowed.",
            )

    comment = Comment(
        content=data.content,
        article_id=article.id,
        author_id=author.id,
        parent_id=data.parent_id,
    )
    db.add(comment)
    await db.flush()

    # Reload with author relationship
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author), selectinload(Comment.replies))
        .where(Comment.id == comment.id)
    )
    return result.scalar_one()


async def delete_comment(
    slug: str,
    comment_id: int,
    current_user: User,
    db: AsyncSession,
) -> None:
    """
    Delete a comment. Only the author or an admin can do this.
    """
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    await db.delete(comment)
    await db.flush()
