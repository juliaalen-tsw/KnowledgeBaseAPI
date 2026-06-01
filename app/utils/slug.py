"""
utils/slug.py
-------------
Generates URL-safe slugs from article titles.

A slug is the URL-friendly version of a title:
  "My First Article!" -> "my-first-article"
  "Hello World 2024" -> "hello-world-2024"

If a slug already exists in the DB, we append a number:
  "my-first-article" exists -> try "my-first-article-2" -> "my-first-article-3" etc.
"""
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.article import Article


def generate_slug(title: str) -> str:
    """Convert a title string into a URL-safe slug."""
    return slugify(title)


async def get_unique_slug(title: str, db: AsyncSession, exclude_id: int | None = None) -> str:
    """
    Generate a slug that doesn't already exist in the database.
    
    Args:
        title: The article title to slugify
        db: Database session for checking existing slugs
        exclude_id: If updating an article, exclude its own ID from the check
    
    Returns:
        A unique slug string
    """
    base_slug = generate_slug(title)
    slug = base_slug
    counter = 2

    while True:
        # Check if this slug already exists
        query = select(Article).where(Article.slug == slug)
        if exclude_id:
            query = query.where(Article.id != exclude_id)
        
        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        if not existing:
            return slug  # This slug is available!

        # Slug exists, try with a number suffix
        slug = f"{base_slug}-{counter}"
        counter += 1
