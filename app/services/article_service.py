"""
services/article_service.py
----------------------------
Business logic for article CRUD operations.
"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.article import Article, ArticleStatus
from app.models.tag import Tag
from app.models.user import User, UserRole
from app.schemas.article import ArticleCreate, ArticleUpdate
from app.utils.slug import get_unique_slug


def _article_with_relations():
    """
    Helper that returns a query loading article WITH author and tags in one DB query.
    
    'selectinload' is an eager loading strategy - it fetches related data
    in a separate but efficient query, avoiding the N+1 query problem.
    (N+1 problem: fetching 10 articles then making 10 more queries for authors = 11 queries)
    With selectinload: 2 queries total, regardless of result count.
    """
    return (
        select(Article)
        .options(
            selectinload(Article.author),
            selectinload(Article.tags),
        )
    )


async def get_published_articles(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    tag_slug: str | None = None,
) -> dict:
    """
    Get paginated list of published articles.
    Optionally filter by tag slug.
    """
    query = (
        _article_with_relations()
        .where(Article.status == ArticleStatus.PUBLISHED)
        .order_by(Article.published_at.desc())
    )

    if tag_slug:
        query = query.join(Article.tags).where(Tag.slug == tag_slug)

    # Count total for pagination metadata
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination: offset = how many rows to skip
    offset = (page - 1) * per_page
    result = await db.execute(query.offset(offset).limit(per_page))
    articles = list(result.scalars().unique().all())

    return {
        "items": articles,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, -(-total // per_page)),  # Ceiling division
    }


async def get_article_by_slug(slug: str, db: AsyncSession) -> Article:
    """
    Get a single published article by slug and increment its view count.
    """
    result = await db.execute(
        _article_with_relations()
        .where(Article.slug == slug)
        .where(Article.status == ArticleStatus.PUBLISHED)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Increment view count
    article.view_count += 1
    db.add(article)
    await db.flush()
    return article


async def get_my_drafts(author: User, db: AsyncSession) -> list[Article]:
    """Get all DRAFT articles belonging to the current user."""
    result = await db.execute(
        _article_with_relations()
        .where(Article.author_id == author.id)
        .where(Article.status == ArticleStatus.DRAFT)
        .order_by(Article.created_at.desc())
    )
    return list(result.scalars().unique().all())


async def create_article(data: ArticleCreate, author: User, db: AsyncSession) -> Article:
    """
    Create a new article.
    
    Business rules:
    - Slug is auto-generated from title
    - If status is PUBLISHED, set published_at timestamp
    - Tags are linked by their IDs
    """
    slug = await get_unique_slug(data.title, db)

    article = Article(
        title=data.title,
        slug=slug,
        content=data.content,
        summary=data.summary,
        author_id=author.id,
        status=data.status,
        published_at=datetime.now(timezone.utc) if data.status == ArticleStatus.PUBLISHED else None,
    )

    # Link tags
    if data.tag_ids:
        tag_result = await db.execute(select(Tag).where(Tag.id.in_(data.tag_ids)))
        article.tags = list(tag_result.scalars().all())

    db.add(article)
    await db.flush()

    # Reload with relationships
    result = await db.execute(
        _article_with_relations().where(Article.id == article.id)
    )
    return result.scalar_one()


async def update_article(
    slug: str,
    data: ArticleUpdate,
    current_user: User,
    db: AsyncSession,
) -> Article:
    """
    Update an article.
    
    Business rules:
    - Only the author or an admin can update
    - published_at is only set ONCE (when first published)
    - Slug regenerates if title changes
    """
    result = await db.execute(
        _article_with_relations().where(Article.slug == slug)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Authorization check
    if article.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to update this article")

    if data.title is not None:
        article.title = data.title
        article.slug = await get_unique_slug(data.title, db, exclude_id=article.id)

    if data.content is not None:
        article.content = data.content

    if data.summary is not None:
        article.summary = data.summary

    if data.status is not None:
        # Set published_at only once - when first published
        if data.status == ArticleStatus.PUBLISHED and article.published_at is None:
            article.published_at = datetime.now(timezone.utc)
        article.status = data.status

    if data.tag_ids is not None:
        tag_result = await db.execute(select(Tag).where(Tag.id.in_(data.tag_ids)))
        article.tags = list(tag_result.scalars().all())

    db.add(article)
    await db.flush()
    await db.refresh(article)
    return article


async def delete_article(slug: str, current_user: User, db: AsyncSession) -> Article:
    """
    Soft-delete an article by setting its status to ARCHIVED.
    The record stays in the database but disappears from all public listings.
    """
    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if article.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete this article")

    article.status = ArticleStatus.ARCHIVED
    db.add(article)
    await db.flush()
    return article


async def toggle_featured(slug: str, db: AsyncSession) -> Article:
    """Admin-only: toggle the is_featured flag on an article."""
    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.is_featured = not article.is_featured
    db.add(article)
    await db.flush()
    await db.refresh(article)
    return article
