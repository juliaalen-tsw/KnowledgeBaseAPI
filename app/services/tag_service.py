"""
services/tag_service.py
-----------------------
Business logic for tag management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException
from app.models.tag import Tag
from app.models.article import Article, article_tags, ArticleStatus
from app.schemas.tag import TagCreate
from slugify import slugify


async def get_all_tags(db: AsyncSession) -> list[dict]:
    """
    Get all tags with a count of how many PUBLISHED articles use each tag.
    
    This uses a SQL JOIN and GROUP BY to count in a single query.
    """
    # Join tags -> article_tags -> articles, filter published, group by tag
    result = await db.execute(
        select(Tag, func.count(Article.id).label("article_count"))
        .outerjoin(article_tags, Tag.id == article_tags.c.tag_id)
        .outerjoin(
            Article,
            (Article.id == article_tags.c.article_id) & (Article.status == ArticleStatus.PUBLISHED),
        )
        .group_by(Tag.id)
        .order_by(Tag.name)
    )
    rows = result.all()
    return [{"id": tag.id, "name": tag.name, "slug": tag.slug, "article_count": count}
            for tag, count in rows]


async def create_tag(data: TagCreate, db: AsyncSession) -> Tag:
    """Create a new tag (Admin only). Names are stored lowercase."""
    name = data.name.lower().strip()
    slug = slugify(name)

    # Check for duplicates
    existing = await db.execute(select(Tag).where(Tag.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tag already exists")

    tag = Tag(name=name, slug=slug)
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


async def get_tag_by_slug(slug: str, db: AsyncSession) -> Tag:
    """Get a tag by slug or raise 404."""
    result = await db.execute(select(Tag).where(Tag.slug == slug))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag
