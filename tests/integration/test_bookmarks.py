"""
tests/integration/test_bookmarks.py
-------------------------------------
Tests for bookmark toggle behavior.
"""

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.article import Article, ArticleStatus
from app.models.user import User
from tests.conftest import auth_headers


async def make_article(db: AsyncSession, author: User, slug: str = "test-article") -> Article:
    article = Article(
        title=slug.replace("-", " ").title(),
        slug=slug,
        content="Content",
        author_id=author.id,
        status=ArticleStatus.PUBLISHED,
        published_at=datetime.now(timezone.utc),
    )
    db.add(article)
    await db.flush()
    return article


@pytest.mark.asyncio
async def test_bookmark_toggle_add(client: AsyncClient, db, test_user, user_token):
    """First bookmark request adds the bookmark."""
    article = await make_article(db, test_user, "bookmarkable-article")
    response = await client.post(
        f"/api/v1/articles/{article.slug}/bookmark",
        headers=auth_headers(user_token),
    )
    assert response.status_code == 200
    assert response.json()["bookmarked"] is True


@pytest.mark.asyncio
async def test_bookmark_toggle_remove(client: AsyncClient, db, test_user, user_token):
    """Second bookmark request removes the bookmark (toggle)."""
    article = await make_article(db, test_user, "toggle-article")

    # Add bookmark
    await client.post(
        f"/api/v1/articles/{article.slug}/bookmark",
        headers=auth_headers(user_token),
    )
    # Toggle off
    response = await client.post(
        f"/api/v1/articles/{article.slug}/bookmark",
        headers=auth_headers(user_token),
    )
    assert response.status_code == 200
    assert response.json()["bookmarked"] is False


@pytest.mark.asyncio
async def test_my_bookmarks(client: AsyncClient, db, test_user, user_token):
    """User can list their bookmarked articles."""
    article = await make_article(db, test_user, "saved-article")
    await client.post(
        f"/api/v1/articles/{article.slug}/bookmark",
        headers=auth_headers(user_token),
    )

    response = await client.get(
        "/api/v1/bookmarks/my",
        headers=auth_headers(user_token),
    )
    assert response.status_code == 200
    slugs = [a["slug"] for a in response.json()]
    assert "saved-article" in slugs
