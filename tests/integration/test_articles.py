"""
tests/integration/test_articles.py
-------------------------------------
Integration tests for article CRUD endpoints.
"""

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.article import Article, ArticleStatus
from app.models.user import User
from tests.conftest import auth_headers


async def create_published_article(db: AsyncSession, author: User, title: str = "Test Article") -> Article:
    """Helper to create a published article directly in the DB."""
    article = Article(
        title=title,
        slug=title.lower().replace(" ", "-"),
        content="Test content body",
        summary="Short summary",
        author_id=author.id,
        status=ArticleStatus.PUBLISHED,
        published_at=datetime.now(timezone.utc),
    )
    db.add(article)
    await db.flush()
    await db.refresh(article)
    return article


@pytest.mark.asyncio
async def test_list_articles_public(client: AsyncClient, db, test_user):
    """Anyone can list published articles without authentication."""
    await create_published_article(db, test_user)
    response = await client.get("/api/v1/articles")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_create_article_authenticated(client: AsyncClient, user_token):
    """Authenticated user can create an article."""
    response = await client.post(
        "/api/v1/articles",
        json={
            "title": "My New Article",
            "content": "This is the article content.",
            "status": "DRAFT",
        },
        headers=auth_headers(user_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My New Article"
    assert data["slug"] == "my-new-article"
    assert data["status"] == "DRAFT"


@pytest.mark.asyncio
async def test_create_article_unauthenticated(client: AsyncClient):
    """Unauthenticated users cannot create articles."""
    response = await client.post(
        "/api/v1/articles",
        json={"title": "Unauthorized", "content": "Test"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_article_by_slug(client: AsyncClient, db, test_user):
    """Anyone can fetch a published article by slug."""
    article = await create_published_article(db, test_user, "Slug Test Article")
    response = await client.get(f"/api/v1/articles/{article.slug}")
    assert response.status_code == 200
    assert response.json()["slug"] == article.slug


@pytest.mark.asyncio
async def test_draft_not_publicly_visible(client: AsyncClient, db, test_user):
    """Draft articles are NOT visible in the public listing."""
    draft = Article(
        title="Hidden Draft",
        slug="hidden-draft",
        content="Private content",
        author_id=test_user.id,
        status=ArticleStatus.DRAFT,
    )
    db.add(draft)
    await db.flush()

    response = await client.get("/api/v1/articles/hidden-draft")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_article_by_author(client: AsyncClient, db, test_user, user_token):
    """An article's author can update it."""
    article = await create_published_article(db, test_user)
    response = await client.patch(
        f"/api/v1/articles/{article.slug}",
        json={"title": "Updated Title"},
        headers=auth_headers(user_token),
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_update_article_not_author(client: AsyncClient, db, test_user, test_admin, admin_token):
    """A non-author (non-admin) cannot update another user's article."""
    # Article owned by test_user, trying to update as admin (who IS allowed)
    # Let's create another regular user instead
    from app.models.user import UserRole
    from app.utils.security import hash_password, create_access_token
    other_user = User(
        email="other@example.com",
        password_hash=hash_password("OtherPass123!"),
        display_name="Other User",
        role=UserRole.MEMBER,
    )
    db.add(other_user)
    await db.flush()
    other_token = create_access_token({"sub": str(other_user.id)})

    article = await create_published_article(db, test_user)
    response = await client.patch(
        f"/api/v1/articles/{article.slug}",
        json={"title": "Hacked Title"},
        headers=auth_headers(other_token),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_article_soft_delete(client: AsyncClient, db, test_user, user_token):
    """Deleting an article archives it (soft delete)."""
    article = await create_published_article(db, test_user)
    response = await client.delete(
        f"/api/v1/articles/{article.slug}",
        headers=auth_headers(user_token),
    )
    assert response.status_code == 204

    # Article should no longer be publicly accessible
    get_response = await client.get(f"/api/v1/articles/{article.slug}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_my_drafts(client: AsyncClient, db, test_user, user_token):
    """User can list their own draft articles."""
    draft = Article(
        title="My Draft",
        slug="my-draft",
        content="Draft content",
        author_id=test_user.id,
        status=ArticleStatus.DRAFT,
    )
    db.add(draft)
    await db.flush()

    response = await client.get(
        "/api/v1/articles/my/drafts",
        headers=auth_headers(user_token),
    )
    assert response.status_code == 200
    slugs = [a["slug"] for a in response.json()]
    assert "my-draft" in slugs
