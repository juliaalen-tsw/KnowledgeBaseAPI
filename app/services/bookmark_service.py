"""
services/bookmark_service.py
-----------------------------
Handles bookmarking (saving) articles.

Toggle behavior: If already bookmarked -> remove it. If not -> add it.
This is called "toggle" because it switches between two states.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.models.bookmark import Bookmark
from app.models.article import Article, ArticleStatus
from app.models.user import User


async def toggle_bookmark(slug: str, user: User, db: AsyncSession) -> dict:
    """
    Toggle a bookmark for the current user on an article.
    
    Returns a dict with 'bookmarked' (bool) and 'message' (str).
    """
    art_result = await db.execute(
        select(Article)
        .where(Article.slug == slug)
        .where(Article.status == ArticleStatus.PUBLISHED)
    )
    article = art_result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Check if bookmark already exists
    bm_result = await db.execute(
        select(Bookmark)
        .where(Bookmark.user_id == user.id)
        .where(Bookmark.article_id == article.id)
    )
    existing = bm_result.scalar_one_or_none()

    if existing:
        # Already bookmarked -> remove it
        await db.delete(existing)
        await db.flush()
        return {"bookmarked": False, "message": "Bookmark removed"}
    else:
        # Not bookmarked -> add it
        bookmark = Bookmark(user_id=user.id, article_id=article.id)
        db.add(bookmark)
        await db.flush()
        return {"bookmarked": True, "message": "Article bookmarked"}


async def get_my_bookmarks(user: User, db: AsyncSession) -> list[Bookmark]:
    """Get all bookmarks for the current user, with article details."""
    result = await db.execute(
        select(Bookmark)
        .options(
            selectinload(Bookmark.article).selectinload(Article.author),
            selectinload(Bookmark.article).selectinload(Article.tags),
        )
        .where(Bookmark.user_id == user.id)
        .order_by(Bookmark.created_at.desc())
    )
    return list(result.scalars().all())
