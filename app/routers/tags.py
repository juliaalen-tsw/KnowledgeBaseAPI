"""
routers/tags.py
---------------
Tag management and article-by-tag filtering.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.dependencies.cache import get_cache, CacheService, TAGS_TTL
from app.dependencies.cache import tags_list_key, tag_articles_key
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagWithCount
from app.schemas.article import ArticleListResponse, PaginatedArticles
from app.services import tag_service, article_service

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get(
    "",
    response_model=list[TagWithCount],
    summary="List all tags with article counts (cached 15 min)",
)
async def list_tags(
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
):
    """Get all tags, each with a count of how many published articles use it."""
    cache_key = tags_list_key()
    cached = await cache.get(cache_key)
    if cached:
        return cached

    tags = await tag_service.get_all_tags(db)
    await cache.set(cache_key, tags, ttl=TAGS_TTL)
    return tags


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tag (Admin only)",
)
async def create_tag(
    data: TagCreate,
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
    _admin: User = Depends(get_current_admin),
):
    """Create a new tag. Only admins can create tags."""
    tag = await tag_service.create_tag(data, db)
    await cache.delete(tags_list_key())  # Invalidate tag list cache
    return tag


@router.get(
    "/{slug}/articles",
    response_model=PaginatedArticles,
    summary="List articles by tag (paginated, cached)",
)
async def articles_by_tag(
    slug: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
):
    """Get published articles filtered by a specific tag."""
    cache_key = tag_articles_key(slug, page, per_page)
    cached = await cache.get(cache_key)
    if cached:
        return cached

    result = await article_service.get_published_articles(db, page, per_page, tag_slug=slug)
    paginated = PaginatedArticles(
        items=[ArticleListResponse.model_validate(a) for a in result["items"]],
        total=result["total"],
        page=result["page"],
        per_page=result["per_page"],
        pages=result["pages"],
    )
    await cache.set(cache_key, paginated.model_dump(mode="json"), ttl=TAGS_TTL)
    return paginated
