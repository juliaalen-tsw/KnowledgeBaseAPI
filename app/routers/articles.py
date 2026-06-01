"""
routers/articles.py
-------------------
Article CRUD endpoints with Redis caching.

Cache strategy used: Cache-Aside (Lazy Loading)
- On GET: check cache first. Cache HIT -> return cached. Cache MISS -> fetch DB, store in cache.
- On write (POST/PATCH/DELETE): invalidate related caches so stale data isn't served.
"""

import json
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.cache import get_cache, CacheService, ARTICLES_TTL, ARTICLE_DETAIL_TTL
from app.dependencies.cache import article_list_key, article_detail_key
from app.models.user import User
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleResponse, ArticleListResponse, PaginatedArticles
from app.services import article_service

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.get(
    "",
    response_model=PaginatedArticles,
    summary="List published articles (paginated, cached)",
)
async def list_articles(
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    tag: str | None = Query(default=None, description="Filter by tag slug"),
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
):
    """
    Get a paginated list of published articles.
    Results are cached for 5 minutes.
    """
    cache_key = article_list_key(page, per_page, tag)

    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Cache miss: fetch from DB
    result = await article_service.get_published_articles(db, page, per_page, tag)

    # Serialize to JSON-compatible dict using Pydantic, then cache it
    paginated = PaginatedArticles(
        items=[ArticleListResponse.model_validate(a) for a in result["items"]],
        total=result["total"],
        page=result["page"],
        per_page=result["per_page"],
        pages=result["pages"],
    )
    await cache.set(cache_key, paginated.model_dump(mode="json"), ttl=ARTICLES_TTL)

    return paginated


@router.get(
    "/my/drafts",
    response_model=list[ArticleListResponse],
    summary="List my draft articles",
)
async def my_drafts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all DRAFT articles authored by the current user. Not cached."""
    articles = await article_service.get_my_drafts(current_user, db)
    return [ArticleListResponse.model_validate(a) for a in articles]


@router.get(
    "/{slug}",
    response_model=ArticleResponse,
    summary="Get article by slug (cached, increments view count)",
)
async def get_article(
    slug: str,
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
):
    """
    Get a single published article by its URL slug.
    The view_count is incremented on every request.
    Cached for 1 minute.
    """
    cache_key = article_detail_key(slug)
    cached = await cache.get(cache_key)
    if cached:
        return cached

    article = await article_service.get_article_by_slug(slug, db)
    response = ArticleResponse.model_validate(article)
    await cache.set(cache_key, response.model_dump(mode="json"), ttl=ARTICLE_DETAIL_TTL)

    return response


@router.post(
    "",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new article",
)
async def create_article(
    data: ArticleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
):
    """
    Create a new article (DRAFT or PUBLISHED).
    Invalidates the article list cache on success.
    """
    article = await article_service.create_article(data, current_user, db)

    # Invalidate cached article lists since a new article was added
    await cache.delete_pattern("articles:list:*")
    await cache.delete_pattern("tags:*")  # Tag article counts may have changed

    return ArticleResponse.model_validate(article)


@router.patch(
    "/{slug}",
    response_model=ArticleResponse,
    summary="Update an article (author or admin only)",
)
async def update_article(
    slug: str,
    data: ArticleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
):
    """
    Update article content, status, or tags.
    Only the article author or an admin can do this.
    """
    article = await article_service.update_article(slug, data, current_user, db)

    # Invalidate this article's cache and the list caches
    await cache.delete(article_detail_key(slug))
    await cache.delete(article_detail_key(article.slug))  # In case slug changed
    await cache.delete_pattern("articles:list:*")
    await cache.delete_pattern("tags:*")

    return ArticleResponse.model_validate(article)


@router.delete(
    "/{slug}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete an article (author or admin only)",
)
async def delete_article(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
):
    """
    Archive an article (soft delete - sets status to ARCHIVED).
    The article remains in the database but disappears from public listings.
    """
    await article_service.delete_article(slug, current_user, db)

    # Remove from cache
    await cache.delete(article_detail_key(slug))
    await cache.delete_pattern("articles:list:*")
    await cache.delete_pattern("tags:*")
